@echo off

echo Building Moses Desktop Application...

pip install pyinstaller

pyinstaller ^
--onefile ^
--noconsole ^
--name Moses ^
app.py

echo.
echo Build Complete.
echo Executable located in dist\\Moses.exe
pause
