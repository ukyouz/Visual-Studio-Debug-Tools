pyinstaller.exe --noconfirm .\guiVSdebugger.spec

@REM MOVE dist\VSdebugger\_internal\view dist\VSdebugger\view
DEL dist\VSdebugger\_internal\PyQt6\Qt6\bin\Qt6Network.dll
DEL dist\VSdebugger\_internal\PyQt6\Qt6\bin\opengl32sw.dll
MOVE dist\VSdebugger\_internal\view dist\VSdebugger



pyinstaller.exe --noconfirm .\guiBinView.spec
MOVE dist\BinView\BinView.exe dist\VSdebugger