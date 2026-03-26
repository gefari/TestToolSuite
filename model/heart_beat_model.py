import logging
logger = logging.getLogger(__name__)

from .heart_beat_manager import HeartBeatManager
from PySide6.QtCore import QObject, Signal
from scipy.interpolate import PchipInterpolator
import numpy as np



class HeartBeatModel(QObject):
    
    waveform_data_changed = Signal()
    sample_rate_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self._sample_per_seconds: int = 1000  # default, overridden by NiDaqMx ViewModel
        self._bpm: int = 60  # default, overridden by heart beat ViewModel

        self._heart_beat_manager = HeartBeatManager()
        self._heart_beat_manager.load_settings()
        self._waveform_reference_points = self._heart_beat_manager.get()
        self._abp_reference_percentage_time_points = [v['time_s'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_pressure_points = [v['pressure_mmHg'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_time_points = []
        
        self._abp_waveform_time_points = []
        self._abp_waveform_pressure_points = []

        self._generate_single_abp_beat()

        self.MIN_SAMPLES_PER_BEAT = 1000

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

    def set_min_sample_per_seconds(self, sps: int) -> None:
        if sps <= 0:
            raise ValueError(f"Sample rate must be positive: {sps}")
        self.MIN_SAMPLES_PER_BEAT = sps
        self.sample_rate_changed.emit(sps)
        self._generate_single_abp_beat()  # triggers waveform_data_changed signal


    def get_sample_per_seconds(self):
        return self._sample_per_seconds

    def set_bpm(self, bpm: int) -> None:
        if not (30 <= bpm <= 240):
            raise ValueError(f"BPM out of physiological range: {bpm}")
        self._bpm = bpm
        self._sample_per_seconds = self._compute_required_sample_rate()  # auto-adapt
        self._generate_single_abp_beat()
        self.sample_rate_changed.emit(self._sample_per_seconds)

    def get_bpm(self):
        return self._bpm

    def set_waveform_points(self, value):
        raise NotImplementedError("Direct waveform point assignment is not supported.")

    def _num_samples_per_beat(self) -> int:
        return max(2, int((self._sample_per_seconds * 60) / self._bpm))

    def _generate_single_abp_beat(self):
        self._abp_reference_time_points.clear()

        num_samples = self._num_samples_per_beat()

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

    def _compute_required_sample_rate(self) -> int:
        """Minimum sample rate to guarantee at least 1000 samples per beat."""
        import math
        return max(self.MIN_SAMPLES_PER_BEAT,
                   math.ceil((self._bpm * self.MIN_SAMPLES_PER_BEAT) / 60))