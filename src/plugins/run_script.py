from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.WidgetScript import Script


class RunScript(Plugin):

    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": "Tool",
                "submenus": [
                    {
                        "name": self.tr("Open Script Window..."),
                        "command": "OpenScriptWindow",
                        "position": 0,
                    },
                    { "name": "---" },
                ],
            },
        ]

    def registerCommands(self) -> list[tuple]:
        return [
            ("OpenScriptWindow", self.open_script_window),
        ]

    def post_init(self):
        self.script = None
        self.app.evt.add_hook("ApplicationClosed", self._onClosed)

    def _onClosed(self, evt):
        if self.script:
            self.script.close()

    def open_script_window(self):
        if self.script is None:
            self.script = Script(self.app)
        self.script.show()
        self.script.activateWindow()