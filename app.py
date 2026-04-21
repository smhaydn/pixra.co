"""
Ticimax AI Manager — Masaustu Uygulamasi (PyQt6)
Giris noktasi. Tum moduller ayri dosyalarda tanimlidir.

Modul Yapisi:
    - theme.py          : QSS tema tanimlari
    - helpers.py        : Yardimci fonksiyonlar ve hata toleransi araclari
    - ai_workers.py     : Arka plan worker thread'leri (Ticimax, Vision, Create)
    - gui_manager.py    : Arayuz bilesenler (LoginPanel, ProductDetailDialog, MainWindow)
    - ticimax_api.py    : Ticimax SOAP client
    - vision_engine.py  : Gemini Vision AI motoru
"""

import sys
from PyQt6.QtWidgets import QApplication
from theme import DARK_THEME_QSS
from gui_manager import MainWindow


def main():
    """Uygulamayi baslatir."""
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
