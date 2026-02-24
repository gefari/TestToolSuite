import logging
logger = logging.getLogger(__name__)

import threading
import usb.core
import nidaqmx
import numpy as np

from nidaqmx.constants import AcquisitionType, RegenerationMode

from PySide6.QtCore import QObject, Signal
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from model.transducer_model import mm_hg_to_volts
from model.heart_beat_model import HeartBeatModel

NI_6216_VID = 0x3923
NI_6216_PID = 0x733B

class Ni6216DaqMx(QObject):
    status_message = Signal(str)
    connection_changed = Signal(bool)
    generation_state_changed = Signal(bool)

    def __init__(self, heart_beat_model: HeartBeatModel, parent=None):
        super().__init__(parent)
        self._heart_beat_model = heart_beat_model
        self._task_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._is_connected = False
        self._task = None

        self.ACTIVE_SEARCH_SLEEP_S = 1
        self.SINGLE_ENDED_REF_VOLTAGE = 0.0

        self.SAMPLES_PER_SECOND = 1000

        # Build initial waveform from HeartBeatModel
        self._ao0_waveform = None
        self._ao1_ref = None
        self._sync_waveform()

        # React to future waveform changes
        self._heart_beat_model.waveform_data_changed.connect(self._on_waveform_changed)

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_generating(self) -> bool:
        return self._task is not None

    def _set_connected(self, value: bool):
        if self._is_connected != value:
            self._is_connected = value
            self.connection_changed.emit(value)
            # If device is unplugged mid-generation, stop the task
            if not value and self.is_generating:
                self.stop_generation()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                device = usb.core.find(idVendor=NI_6216_VID, idProduct=NI_6216_PID)
                if device is not None:
                    self._set_connected(True)
                    self.status_message.emit(
                        f"NI-6216 Connected:"
                        f"[VID:{device.idVendor:04X},PID:{device.idProduct:04X}]"
                    )
                else:
                    self._set_connected(False)
                    self.status_message.emit("NI-6216: device not found.")
            except Exception as e:
                error_msg = f"USB error: {e}"
                self._set_connected(False)
                self.status_message.emit(error_msg)
                logger.warning(error_msg)
            self._stop_event.wait(self.ACTIVE_SEARCH_SLEEP_S)

    def start_generation(self):
        with self._task_lock:
            if self._task is not None or not self._is_connected:
                return
            if self._ao0_waveform is None:
                msg = "NI-6216: analog output ch0, no waveform data available."
                self.status_message.emit(msg)
                logger.warning(msg)
                return

            self._task = nidaqmx.Task()
            try:
                samples_per_channel = len(self._ao0_waveform)

                self._task.ao_channels.add_ao_voltage_chan(
                    "Dev1/ao0", min_val=-10.0, max_val=10.0
                )
                self._task.ao_channels.add_ao_voltage_chan(
                    "Dev1/ao1", min_val=-10.0, max_val=10.0
                )
                self._task.timing.cfg_samp_clk_timing(
                    rate=self.SAMPLES_PER_SECOND,
                    sample_mode=AcquisitionType.CONTINUOUS,
                    samps_per_chan=samples_per_channel
                )
                self._task.out_stream.regen_mode = RegenerationMode.ALLOW_REGENERATION

                waveforms = np.ascontiguousarray(
                    np.vstack((self._ao0_waveform, self._ao1_ref))
                )

                AnalogMultiChannelWriter(self._task.out_stream).write_many_sample(waveforms)

                self._task.start()
                self.generation_state_changed.emit(True)
                msg = "NI-6216: waveform generation started."
                logger.debug(msg)
                self.status_message.emit(msg)

            except Exception as e:
                error_msg = f"NI-6216 generation error: {e}"
                self._task.close()
                self._task = None
                logger.warning(error_msg)
                self.status_message.emit(error_msg)

    def stop_generation(self):
        with self._task_lock:
            if self._task is None:
                return
            try:
                self._task.stop()
                self._task.close()
            except Exception as e:
                error_msg = f"NI-6216 stop error: {e}"
                logger.warning(error_msg)
                self.status_message.emit(error_msg)
            finally:
                msg = "NI-6216: waveform generation stopped."
                self._task = None
                self.generation_state_changed.emit(False)
                logger.debug(msg)
                self.status_message.emit(msg)

    def stop(self):
        self.stop_generation()
        self._stop_event.set()
        self._thread.join()

    def _sync_waveform(self):
        """Pull latest pressure points from HeartBeatModel and convert to volts."""
        waveform = self._heart_beat_model.get_waveform_points()
        pressure_points = np.array(waveform['abp_waveform_pressure_points'])

        # Convert mmHg → volts for ao0
        self._ao0_waveform = np.array([mm_hg_to_volts(p) for p in pressure_points])

        # ao1 stays as flat reference voltage
        self._ao1_ref = np.full(len(self._ao0_waveform), self.SINGLE_ENDED_REF_VOLTAGE)

    def _on_waveform_changed(self):
        with self._task_lock:
            if self._task is None:
                return
            """Called from main thread via Qt signal. Calls stop then start — lock acquired separately in each."""
            was_generating = self.is_generating
            if was_generating:
                self.stop_generation() # releases lock before returning
            self._sync_waveform()
            self.status_message.emit("NI-6216: waveform updated from HeartBeat model.")

            if was_generating:
                self.start_generation()  # re-acquires lock
