@REM @echo off


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