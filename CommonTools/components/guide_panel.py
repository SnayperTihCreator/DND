import os
import uuid

from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QWidget, QDockWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-web-security --ignore-certificate-errors'


class GuidePanel(QDockWidget):
    def __init__(self, url, title):
        super().__init__(title)
        
        self.cw = QWidget()
        self.box = QVBoxLayout(self.cw)
        
        navigation_panel = QHBoxLayout()
        
        self.btnBack = QPushButton("←")
        self.btnBack.pressed.connect(self._handle_back)
        navigation_panel.addWidget(self.btnBack)
        self.lineUrl = QLineEdit()
        self.lineUrl.returnPressed.connect(self._handle_load_url)
        navigation_panel.addWidget(self.lineUrl)
        
        self.box.addLayout(navigation_panel)
        
        self.profile = QWebEngineProfile(uuid.uuid4().hex, self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.web_page = QWebEnginePage(self.profile, self)
        self.web_page.urlChanged.connect(self._handle_update_url)
        
        self.webEngine = QWebEngineView()
        self.webEngine.setPage(self.web_page)
        
        self.box.addWidget(self.webEngine)
        
        self._handle_load_url(QUrl(url))
        
        self.setWidget(self.cw)
    
    def _handle_update_url(self, url: QUrl):
        self.lineUrl.setText(url.toString())
    
    def _handle_load_url(self, url=None):
        if url is None:
            url = QUrl(self.lineUrl.text())
        self.webEngine.load(url)
    
    def _handle_back(self):
        self.webEngine.back()
