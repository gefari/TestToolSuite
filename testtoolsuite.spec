from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

datas = [
    ('model/heartBeat.xml', 'model')
]
datas += copy_metadata('nidaqmx')
datas += copy_metadata('numpy')
datas += copy_metadata('scipy')
datas += copy_metadata('nitypes')
datas += collect_data_files('nitypes')
datas += collect_data_files('nidaqmx')
datas += collect_data_files('qtawesome')   # font/icon files

hiddenimports = [
    'scipy',
    'scipy.signal',
    'scipy.interpolate',
    'scipy.ndimage',
    # nidaqmx
    'nidaqmx',
    'nidaqmx.task',
    'nidaqmx.stream_writers',
    'nidaqmx.stream_readers',
    'nidaqmx.constants',
    'nidaqmx.errors',
    'nidaqmx._task_modules',
    'nidaqmx._task_modules.channels',
    'nidaqmx._task_modules.timing',
    'nidaqmx._task_modules.read_functions',
    'nidaqmx._task_modules.write_functions',
    'nitypes',
    'nitypes.waveform',
    'nitypes.scalar',
    # pyusb
    'usb.core',
    'usb.util',
    'usb.backend.libusb1',
    'usb.backend.libusb0',
    # PySide6 extras often missed
    'PySide6.QtSvg',
    'PySide6.QtXml',
    'PySide6.QtPrintSupport',
    'PySide6.QtCharts',
    # qtawesome
    'qtawesome',
    # numpy
    'numpy',
    'numpy.core._multiarray_umath',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TestToolSuite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,      # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,          # replace with 'resources/icon.ico' if you have one
)
