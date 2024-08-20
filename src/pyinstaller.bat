@REM @echo off

SET VER=%1

py -m pytest tests --cov || goto :error
coverage html

pyinstaller.exe --noconfirm .\guiVSdebugger.spec

@REM COPY dist\VSdebugger\_internal\view dist\VSdebugger\view
@REM DEL dist\VSdebugger\_internal\PyQt6\Qt6\bin\Qt6Network.dll
DEL dist\VSdebugger\_internal\PyQt6\Qt6\bin\opengl32sw.dll
MOVE dist\VSdebugger\_internal\scripts dist\VSdebugger\scripts


pyinstaller.exe --noconfirm .\pyqode_backend.spec
COPY dist\pyqode_backend\pyqode_backend.exe dist\VSdebugger\_internal


pyinstaller.exe --noconfirm .\guiBinView.spec
COPY dist\BinViewer\BinViewer.exe dist\VSdebugger

if [%VER%] == [] SET VER=test

echo %VER%

py add_version_txt.py %VER%
COPY about_me.txt dist\VSdebugger
COPY ..\CHANGELOG.md dist\VSdebugger

"C:\Program Files\7-Zip\7z.exe" a -t7z .\dist\VSdebugger_%VER%.7z .\dist\VSdebugger\

@REM Restore My App Settings
COPY app.ini dist\VSdebugger

:error
exit /b %ERRORLEVEL%add log view in VSDebugger