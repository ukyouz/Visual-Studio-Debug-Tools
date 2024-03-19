from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin


class AboutMe(Plugin):

    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": "Help",
                "submenus": [
                    {
                        "name": "About Me...",
                        "command": "ShowAboutMe",
                    },
                ]
            },
        ]

    def registerCommands(self):
        return [
            ("ShowAboutMe", self.show_about_me),
        ]

    def show_about_me(self):
        with open("about_me.txt", "r") as fs:
            txt = fs.read()

        QtWidgets.QMessageBox.about(
            self.app,
            self.__class__.__name__,
            txt,
        )
