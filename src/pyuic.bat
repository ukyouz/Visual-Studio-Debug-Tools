@REM ..\venv\Lib\site-packages\qt6_applications\Qt\bin\rcc.exe -g python .\view\resource.qrc | sed '0,/PySide6/s//PyQt6/' > .\view\resource.py
..\venv\Lib\site-packages\qt6_applications\Qt\bin\lrelease.exe .\langs\ja_JP.ts -qm .\langs\ja_JP.qm
pyuic6.exe .\view\BinView.ui -o .\view\BinView.py
pyuic6.exe .\view\WidgetBinParser.ui -o .\view\WidgetBinParser.py
pyuic6.exe .\view\VSdebugger.ui -o .\view\VSdebugger.py
pyuic6.exe .\view\WidgetExpression.ui -o .\view\WidgetExpression.py
pyuic6.exe .\view\WidgetMemory.ui -o .\view\WidgetMemory.py
pyuic6.exe .\view\WidgetProcessSelector.ui -o .\view\WidgetProcessSelector.py
pyuic6.exe .\view\WidgetDockTitleBar.ui -o .\view\WidgetDockTitleBar.py
pyuic6.exe .\view\WidgetPicklePdb.ui -o .\view\WidgetPicklePdb.py
pyuic6.exe .\view\WidgetScript.ui -o .\view\WidgetScript.py
