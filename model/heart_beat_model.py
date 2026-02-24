import logging
logger = logging.getLogger(__name__)

from .heart_beat_manager import HeartBeatManager
from PySide6.QtCore import QObject, Signal
from scipy.interpolate import PchipInterpolator
import numpy as np

class HeartBeatModel(QObject):
    
    waveform_data_changed = Signal()

    def __init__(self):
        super().__init__()

        self._num_of_samples_per_HeartBeat = 1000

        self._heart_beat_manager = HeartBeatManager()
        self._heart_beat_manager.load_settings()
        self._waveform_reference_points = self._heart_beat_manager.get()
        self._abp_reference_percentage_time_points = [v['time_s'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_pressure_points = [v['pressure_mmHg'] for v in self._waveform_reference_points['abp_waveform_features'].values()]
        self._abp_reference_time_points = []
        
        self._abp_waveform_time_points = []
        self._abp_waveform_pressure_points = []

        self.generate_single_abp_beat(self._num_of_samples_per_HeartBeat)

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

    def set_waveform_points(self, value):
        raise NotImplementedError("Direct waveform point assignment is not supported.")
    
    def generate_single_abp_beat(self, num_of_samples_per_heart_beat):
        self._abp_reference_time_points.clear()

        for time_point in self._abp_reference_percentage_time_points: 
            if time_point == 0:
                self._abp_reference_time_points.append(0)
            else:
                self._abp_reference_time_points.append(int((time_point * num_of_samples_per_heart_beat) - 1))
        
        logger.debug(f"Generating ABP waveform with reference time points [samples]: {self._abp_reference_time_points}")
        logger.debug(f"Generating ABP waveform with reference pressure points [mmHg]: {self._abp_reference_pressure_points}")
                
        # Sort time and corresponding pressure points together
        zip_points = zip(self._abp_reference_time_points, self._abp_reference_pressure_points)
        sorted_points = sorted(zip_points)
        intermediate_time_points, intermediate_pressure_points = zip(*sorted_points)

        # Point Interpolation
        interpolated_points = PchipInterpolator(intermediate_time_points, intermediate_pressure_points)

        t = np.linspace(start=0,
                              stop=num_of_samples_per_heart_beat - 1,
                              num=num_of_samples_per_heart_beat, 
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
        self.generate_single_abp_beat(self._num_of_samples_per_HeartBeat)
    
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
        self.generate_single_abp_beat(self._num_of_samples_per_HeartBeat)
