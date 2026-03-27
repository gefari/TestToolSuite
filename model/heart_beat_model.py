import logging
logger = logging.getLogger(__name__)

from .heart_beat_manager import HeartBeatManager
from PySide6.QtCore import QObject, Signal
from scipy.interpolate import PchipInterpolator
import numpy as np



class HeartBeatModel(QObject):
    
    waveform_data_changed = Signal()
    sample_rate_changed = Signal(int)
    bpm_changed = Signal(int)
    pulse_duration_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self._sample_per_seconds: int = 1000
        self._pulse_duration_ms: int = 0
        self._bpm: int = 0

        self._heart_beat_manager = HeartBeatManager()
        self._heart_beat_manager.load_settings()
        self._waveform_reference_points = self._heart_beat_manager.get()
        self._abp_reference_percentage_time_points = [v['time_s'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_pressure_points = [v['pressure_mmHg'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_time_points = []
        
        self._abp_waveform_time_points = []
        self._abp_waveform_pressure_points = []

    def get_waveform_points(self):
        return {
            'abp_waveform_time_points': self._abp_waveform_time_points,
            'abp_waveform_pressure_points': self._abp_waveform_pressure_points
        }
    
    def get_waveform_reference_points(self):
        return {
            'abp_ref_waveform_time_points': self._abp_reference_time_points,
            'abp_ref_waveform_pressure_points': self._abp_reference_pressure_points
        }

    # PULSE DURATION
    def set_pulse_duration_ms(self, pulse_duration_ms: int) -> None:
        self._pulse_duration_ms = pulse_duration_ms
        self._bpm = self._pulse_duration_to_bpm(pulse_duration_ms)
        self.pulse_duration_changed.emit(pulse_duration_ms)
        self._generate_single_abp_beat()

    def get_pulse_duration_ms(self) -> int:
        return self._pulse_duration_ms

    # SAMPLE PER SECOND
    def set_sample_per_seconds(self, sps: int) -> None:
        if sps <= 0:
            raise ValueError(f"Sample rate must be positive: {sps}")
        self._sample_per_seconds = sps
        self.sample_rate_changed.emit(sps)
        self._generate_single_abp_beat()

    def get_sample_per_seconds(self):
        return self._sample_per_seconds

    # BPM
    def set_bpm(self, bpm: int) -> None:
        if not (30 <= bpm <= 240):
            raise ValueError(f"BPM out of physiological range: {bpm}")
        self._bpm = bpm
        self._pulse_duration_ms = self._bpm_to_pulse_duration(bpm)
        self.sample_rate_changed.emit(self._sample_per_seconds)
        self._generate_single_abp_beat()

    def get_bpm(self):
        return self._bpm

    def set_waveform_points(self, value):
        raise NotImplementedError("Direct waveform point assignment is not supported.")

    def _calculate_num_samples_per_beat(self) -> int:
        if self._pulse_duration_ms != 0 and self._sample_per_seconds != 0:
            return int(self._pulse_duration_ms * (self._sample_per_seconds / 1000))
        else:
            raise ValueError(f"Something is zero in heart beat model!")

    def _generate_single_abp_beat(self):

        self._abp_reference_time_points.clear()

        num_samples = self._calculate_num_samples_per_beat()
        if num_samples <= 0:
            raise ValueError(f"Num sample must be positive: {num_samples}")
        else:
            for time_point in self._abp_reference_percentage_time_points:
                if time_point == 0:
                    self._abp_reference_time_points.append(0)
                else:
                    self._abp_reference_time_points.append(int((time_point * num_samples) - 1))

            logger.debug(f"Generating ABP waveform with reference time points [samples]: {self._abp_reference_time_points}")
            logger.debug(f"Generating ABP waveform with reference pressure points [mmHg]: {self._abp_reference_pressure_points}")

            # Sort time and corresponding pressure points together
            zip_points = zip(self._abp_reference_time_points, self._abp_reference_pressure_points)
            sorted_points = sorted(zip_points)
            intermediate_time_points, intermediate_pressure_points = zip(*sorted_points)

            # Point Interpolation
            interpolated_points = PchipInterpolator(intermediate_time_points, intermediate_pressure_points)

            t = np.linspace(start=0,
                                  stop=num_samples - 1,
                                  num=num_samples,
                                  retstep=False,
                                  endpoint=True)

            self._abp_waveform_time_points = t
            self._abp_waveform_pressure_points = interpolated_points(t)
            self.waveform_data_changed.emit()
    
    def update_reference_point(self, key, new_time_pct, new_pressure):
        self._waveform_reference_points['abp_waveform_features'][key]['time_s'] = new_time_pct
        self._waveform_reference_points['abp_waveform_features'][key]['pressure_mmHg'] = new_pressure
        # Re-extract and regenerate
        self._abp_reference_percentage_time_points = [v['time_s'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_pressure_points = [v['pressure_mmHg'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._generate_single_abp_beat()
    
    def get_reference_point_keys(self) -> list:
        return list(self._waveform_reference_points['abp_waveform_features'].keys())
    
    def load_default_settings(self):
        self._heart_beat_manager.load_settings()
        self._waveform_reference_points = self._heart_beat_manager.get()
        self._abp_reference_percentage_time_points = [
            v['time_s'] for v in self._waveform_reference_points['abp_waveform_features'].values()
        ]
        self._abp_reference_pressure_points = [
            v['pressure_mmHg'] for v in self._waveform_reference_points['abp_waveform_features'].values()
        ]
        self._generate_single_abp_beat()

    @staticmethod
    def _bpm_to_pulse_duration(bpm: int) -> int:

        num_of_pulses_per_second = bpm/60
        pulse_duration_s = 1/num_of_pulses_per_second
        pulse_duration_ms = int(pulse_duration_s * 1000)
        return pulse_duration_ms


    @staticmethod
    def _pulse_duration_to_bpm(pulse_duration_ms: int) -> int:
        num_of_pulses_per_s = 1000/pulse_duration_ms
        bpm = int(num_of_pulses_per_s * 60)
        return bpm

