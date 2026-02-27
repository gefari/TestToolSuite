@echo off
echo Installing dependencies...
pip install pyinstaller

echo Building TestToolSuite...
python -m PyInstaller testtoolsuite.spec --clean --noconfirm

echo Done. Executable is in dist\TestToolSuite.exe
pause