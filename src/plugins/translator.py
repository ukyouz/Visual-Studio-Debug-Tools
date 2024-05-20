from PyQt6 import QtCore
from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin


class Translator(Plugin):

    def post_init(self):
        self.translator = QtCore.QTranslator()

        if val := self.app.app_setting.value("app/lang", ""):
            self.tranlate_ui(val)

    def registerMenues(self) -> list[MenuAction]:
        val = self.app.app_setting.value("app/lang", "")
        return [
            {
                "name": self.tr("Languages"),
                "actionGroup": True,
                "submenus": [
                    {
                        "name": "English",
                        "command": "SetLanguageEnglish",
                        "checked": val == "",
                    },
                    {
                        "name": "日本語",
                        "command": "SetLanguageJapanese",
                        "checked": val == "ja_JP",
                    },
                ],
            },
        ]

    def registerCommands(self) -> list[tuple]:
        return [
            ("SetLanguageEnglish", lambda: self.tranlate_ui("")),
            ("SetLanguageJapanese", lambda: self.tranlate_ui("ja_JP")),
        ]

    def tranlate_ui(self, lang):
        _app = QtWidgets.QApplication.instance()
        if lang:
            self.translator.load(str(self.app.app_dir / ("langs/%s" % lang)))
            _app.installTranslator(self.translator)
            self.app.app_setting.setValue("app/lang", lang)
        elif self.translator:
            _app.removeTranslator(self.translator)
            self.app.app_setting.remove("app/lang")
        self.app.ui.retranslateUi(self.app)