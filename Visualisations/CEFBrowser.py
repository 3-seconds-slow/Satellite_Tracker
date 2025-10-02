import os
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from cefpython3 import cefpython as cef


class CefBrowser(QWidget):
    def __init__(self, url="", parent=None):
        super().__init__(parent)
        self.browser = None
        self.url = url

        # Timer to pump the CEF message loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.cef_loop)
        self.timer.start(10)

    def cef_loop(self):
        cef.MessageLoopWork()

    def load(self, url: str):
        """Load a new URL or file into the browser."""
        if self.browser:
            self.browser.LoadUrl(url)
        else:
            self.url = url

    def showEvent(self, event):
        if not self.browser:
            window_info = cef.WindowInfo()
            rect = [0, 0, self.width(), self.height()]
            window_info.SetAsChild(int(self.winId()), rect)
            self.browser = cef.CreateBrowserSync(window_info, url=self.url)
        super().showEvent(event)

    def resizeEvent(self, event):
        if self.browser:
            rect = [0, 0, self.width(), self.height()]
            self.browser.SetBounds(*rect)
        super().resizeEvent(event)
