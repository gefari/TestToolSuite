import xml.etree.ElementTree as ET
import os
import inspect
from pathlib import Path

class HeartBeatManager:
    def __init__(self, filename: Path = Path("model") / "heartBeat.xml"):
        self._filename = filename
        base = self.get_settings_path()
        if base is None:
            raise RuntimeError("Unsupported operating system.")
        self._heart_beat_settings_path = Path(base) / self._filename
        self._waveform_dictionary = {}
    
    def _parse_waveform_xml(self) -> dict:
        tree = ET.parse(self._heart_beat_settings_path)   # raises ParseError if malformed
        root = tree.getroot()
        result = {}
        for waveform in root:
            points = {}
            for point in waveform:
                name = point.get('name')
                if name is None:
                    raise ValueError(f"Reference point missing 'name' attribute in <{waveform.tag}>")
                points[name] = {
                    'time_s':        float(point.get('time_s')),
                    'pressure_mmHg': float(point.get('pressure_mmHg'))
                }
            result[waveform.tag] = points
        return result

        
    def get(self) -> dict:
        if not self._waveform_dictionary:
            raise RuntimeError(
                "Waveform settings are not loaded. Call load_settings() first."
            )
        return self._waveform_dictionary

    
    def get_settings_path(self) -> Path:
        if os.name == "nt":
            # Resolve relative to this source file's parent directory
            return Path(__file__).resolve().parent.parent
        else:
            xdg = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            return Path(xdg) / "heartbeat_app"
    
    def load_settings(self):
        path = Path(self._heart_beat_settings_path)
        if not path.exists():
            raise FileNotFoundError(
                f"HeartBeat settings file not found: {path}"
            )
        self._waveform_dictionary = self._parse_waveform_xml()
        if not self._waveform_dictionary:
            raise ValueError(
                f"HeartBeat settings file parsed as empty: {path}"
            )

    def save_settings(self):
        raise NotImplementedError("save_settings() is not yet implemented.")