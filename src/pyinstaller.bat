pyinstaller.exe --noconfirm .\guiVSdebugger.spec

@REM COPY dist\VSdebugger\_internal\view dist\VSdebugger\view
@REM DEL dist\VSdebugger\_internal\PyQt6\Qt6\bin\Qt6Network.dll
DEL dist\VSdebugger\_internal\PyQt6\Qt6\bin\opengl32sw.dll


pyinstaller.exe --noconfirm .\pyqode_backend.spec
COPY dist\pyqode_backend\pyqode_backend.exe dist\VSdebugger\_internal


pyinstaller.exe --noconfirm .\guiBinView.spec
COPY dist\BinView\BinView.exe dist\VSdebugger