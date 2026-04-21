"""
Ticimax AI Manager — Arayuz Yoneticisi (GUI Manager)
LoginPanel, ProductDetailDialog ve MainWindow siniflarini icerir.
Tum kullanici arayuzu bilesenleri bu dosyada merkezlestirilmistir.
"""

import random
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QInputDialog, QCheckBox, QSplitter,
    QGroupBox, QStackedWidget, QFrame, QAbstractItemView, QComboBox,
    QDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QIcon

from ticimax_api import TicimaxClient
from vision_engine import ProductAIContent
from helpers import (
    get_field, load_saved_firms, save_firms_to_file, SessionState
)
from ai_workers import TicimaxWorker, VisionWorker, CreateModeWorker


# ──────────────── LOGIN PANELI ────────────────

class LoginPanel(QWidget):
    """Kullanicinin Ticimax ve Gemini bilgilerini girdigi giris ekrani.
    Firma bilgileri firms.json dosyasinda saklanir ve dropdown ile secilir."""
    from PyQt6.QtCore import pyqtSignal
    connect_requested = pyqtSignal(str, str, str)  # url, uye_kodu, gemini_key

    def __init__(self):
        """LoginPanel olusturucusu."""
        super().__init__()
        self.firms = load_saved_firms()
        self._build_ui()

    def _build_ui(self):
        """Giris ekrani arayuzunu olusturur."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # Baslik
        title = QLabel("TICIMAX AI MANAGER")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00BFA6; letter-spacing: 3px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("SEO & GEO Otomasyon Araci")
        subtitle.setStyleSheet("font-size: 14px; color: #8e8ea0; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # ── Kayitli Firmalar ──
        saved_group = QGroupBox("Kayitli Firmalar")
        saved_layout = QHBoxLayout(saved_group)

        self.combo_firms = QComboBox()
        self.combo_firms.addItem("-- Yeni Firma Ekle --")
        for firm in self.firms:
            self.combo_firms.addItem(firm.get("site", "?"))
        self.combo_firms.currentIndexChanged.connect(self._on_firm_selected)
        saved_layout.addWidget(self.combo_firms, stretch=1)

        btn_delete = QPushButton("Sil")
        btn_delete.setObjectName("dangerBtn")
        btn_delete.setFixedWidth(60)
        btn_delete.clicked.connect(self._delete_firm)
        saved_layout.addWidget(btn_delete)

        layout.addWidget(saved_group)

        # ── Form grubu ──
        form_group = QGroupBox("Baglanti Bilgileri")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(12)

        # Site Adresi
        lbl_url = QLabel("Site Adresi:")
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("ornek: www.lolaofshine.com")
        form_layout.addWidget(lbl_url)
        form_layout.addWidget(self.input_url)

        # WS Yetki Kodu
        lbl_ws = QLabel("WS Yetki Kodu:")
        self.input_ws = QLineEdit()
        self.input_ws.setPlaceholderText("ABCXYZ1234...")
        self.input_ws.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(lbl_ws)
        form_layout.addWidget(self.input_ws)

        # Gemini Key
        lbl_gem = QLabel("Gemini API Key:")
        self.input_gemini = QLineEdit()
        self.input_gemini.setPlaceholderText("AIzaSy...")
        self.input_gemini.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(lbl_gem)
        form_layout.addWidget(self.input_gemini)

        # Kaydet checkbox
        self.chk_save = QCheckBox("Bu firmayi kaydet")
        self.chk_save.setChecked(True)
        form_layout.addWidget(self.chk_save)

        layout.addWidget(form_group)

        # Baglan butonu
        self.btn_connect = QPushButton("BAGLAN")
        self.btn_connect.setFixedHeight(48)
        self.btn_connect.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.btn_connect.clicked.connect(self._on_connect)
        layout.addWidget(self.btn_connect)

        # Durum
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def _on_firm_selected(self, index: int):
        """Dropdown'dan firma secildiginde alanlari doldurur."""
        if index <= 0:
            # "Yeni Firma Ekle" secildi — alanlari temizle
            self.input_url.clear()
            self.input_ws.clear()
            self.input_gemini.clear()
            return
        firm = self.firms[index - 1]
        self.input_url.setText(firm.get("site", ""))
        self.input_ws.setText(firm.get("ws_kodu", ""))
        self.input_gemini.setText(firm.get("gemini_key", ""))

    def _delete_firm(self):
        """Secili firmayi listeden siler."""
        index = self.combo_firms.currentIndex()
        if index <= 0:
            return
        firma_adi = self.combo_firms.currentText()
        yanit = QMessageBox.question(
            self, "Firma Sil",
            f"'{firma_adi}' firmasini silmek istediginize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if yanit == QMessageBox.StandardButton.Yes:
            del self.firms[index - 1]
            save_firms_to_file(self.firms)
            self.combo_firms.removeItem(index)
            self.combo_firms.setCurrentIndex(0)
            self.input_url.clear()
            self.input_ws.clear()
            self.input_gemini.clear()

    def _on_connect(self):
        """Kullanici Baglan butonuna bastiginda calisir."""
        site = self.input_url.text().strip()
        ws = self.input_ws.text().strip()
        gem = self.input_gemini.text().strip()
        if not site or not ws or not gem:
            self.lbl_status.setText("Tum alanlari doldurmalisiniz!")
            return

        # Firmayı kaydet (checkbox isareteliyse)
        if self.chk_save.isChecked():
            site_clean = site.replace("https://", "").replace("http://", "").rstrip("/")
            found = False
            for firm in self.firms:
                if firm.get("site", "") == site_clean:
                    firm["ws_kodu"] = ws
                    firm["gemini_key"] = gem
                    found = True
                    break
            if not found:
                self.firms.append({"site": site_clean, "ws_kodu": ws, "gemini_key": gem})
                self.combo_firms.addItem(site_clean)
            save_firms_to_file(self.firms)

        # Site adresinden WSDL URL olustur
        site = site.replace("https://", "").replace("http://", "").rstrip("/")
        if "/Servis/" in site:
            wsdl_url = f"https://{site}" if not site.startswith("http") else site
        else:
            wsdl_url = f"https://{site}/Servis/UrunServis.svc?wsdl"
        self.lbl_status.setText("")
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Baglaniyor...")
        self.connect_requested.emit(wsdl_url, ws, gem)

    def reset_button(self):
        """Buton durumunu sifirlar."""
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("BAGLAN")


# ──────────────── URUN DETAY DIALOG ────────────────

class ProductDetailDialog(QDialog):
    """Urun AI analiz sonuclarini detayli gosteren popup pencere."""

    def __init__(self, parent, row_idx: int, urun_data, ai_result=None, resim_urls=None):
        """ProductDetailDialog olusturucusu."""
        super().__init__(parent)
        self.setWindowTitle(f"Urun Detayi — Satir {row_idx + 1}")
        self.setMinimumSize(750, 700)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QLabel { color: #e0e0e0; }
            QScrollArea { border: none; background-color: #1a1a2e; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll alani
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(12)

        # Mevcut urun bilgileri
        urun_adi = get_field(urun_data, 'UrunAdi') or '?'
        stok_kodu = get_field(urun_data, 'StokKodu') or '?'
        marka = get_field(urun_data, 'Marka') or '?'
        urun_id = get_field(urun_data, 'ID') or '?'

        scroll_layout.addWidget(self._section_header("MEVCUT URUN BILGILERI"))
        scroll_layout.addWidget(self._info_card([
            ("Urun ID", str(urun_id)),
            ("Stok Kodu", str(stok_kodu)),
            ("Marka", str(marka)),
            ("Mevcut Urun Adi", str(urun_adi)),
        ]))

        # Gorsel bilgisi
        gorsel_sayisi = len(resim_urls) if resim_urls else 0
        scroll_layout.addWidget(self._section_header(f"GORSELLER ({gorsel_sayisi} adet)"))
        if resim_urls:
            gorsel_text = "\n".join([f"  {i+1}. {url}" for i, url in enumerate(resim_urls)])
            lbl = QLabel(gorsel_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #8e8ea0; font-size: 11px; padding: 8px; background-color: #0f0f23; border-radius: 6px;")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            scroll_layout.addWidget(lbl)

        # AI sonuclari
        if ai_result:
            scroll_layout.addWidget(self._section_header("AI ANALIZ SONUCLARI", accent=True))

            # Onerilen Urun Adi
            scroll_layout.addWidget(self._labeled_box(
                "AI Urun Adi", ai_result.urun_adi, "#00BFA6"
            ))

            # SEO Baslık + karakter sayisi
            seo_baslik = ai_result.seo_baslik
            seo_len = len(seo_baslik)
            seo_color = "#00BFA6" if seo_len <= 60 else "#e74c3c"
            scroll_layout.addWidget(self._labeled_box(
                f"SEO Baslik ({seo_len}/60 karakter)", seo_baslik, seo_color
            ))

            # SEO Aciklama + karakter sayisi
            seo_aciklama = ai_result.seo_aciklama
            desc_len = len(seo_aciklama)
            desc_color = "#00BFA6" if desc_len <= 155 else "#e74c3c"
            scroll_layout.addWidget(self._labeled_box(
                f"SEO Aciklama ({desc_len}/155 karakter)", seo_aciklama, desc_color
            ))

            # SEO Anahtar Kelimeler
            scroll_layout.addWidget(self._labeled_box(
                "SEO Anahtar Kelimeler", ai_result.seo_anahtarkelime, "#8e8ea0"
            ))

            # Anahtar Kelimeler (magaza ici)
            scroll_layout.addWidget(self._labeled_box(
                "Anahtar Kelimeler", ai_result.anahtar_kelime, "#8e8ea0"
            ))

            # Odak Anahtar Kelime
            hedef_ak = getattr(ai_result, 'hedef_anahtar_kelime', '')
            if hedef_ak:
                scroll_layout.addWidget(self._labeled_box(
                    "Odak Anahtar Kelime (Focus Keyword)", hedef_ak, "#FFD54F"
                ))

            # Gorsel Alt Text
            gorsel_alt = getattr(ai_result, 'gorsel_alt_text', '')
            if gorsel_alt:
                alt_len = len(gorsel_alt)
                alt_color = "#00BFA6" if alt_len <= 125 else "#e74c3c"
                scroll_layout.addWidget(self._labeled_box(
                    f"Gorsel Alt Text ({alt_len}/125 karakter)", gorsel_alt, alt_color
                ))

            # Onyazi
            scroll_layout.addWidget(self._labeled_box(
                "On Yazi", ai_result.onyazi, "#B388FF"
            ))

            # GEO Ozet (AI citability)
            geo_ozet = getattr(ai_result, 'geo_ozet', '')
            if geo_ozet:
                scroll_layout.addWidget(self._section_header("GEO OZET (AI Alinti Metni)", accent=True))
                geo_lbl = QLabel(geo_ozet)
                geo_lbl.setWordWrap(True)
                geo_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                geo_lbl.setStyleSheet("""
                    color: #e0e0e0; font-size: 13px; padding: 12px;
                    background-color: #0a3d5c; border-left: 4px solid #00BFA6;
                    border-radius: 4px; font-style: italic;
                """)
                scroll_layout.addWidget(geo_lbl)

            # Neden Bu Urun (E-E-A-T)
            neden = getattr(ai_result, 'neden_bu_urun', '')
            if neden:
                scroll_layout.addWidget(self._section_header("NEDEN BU URUN (E-E-A-T)"))
                neden_lbl = QLabel(neden)
                neden_lbl.setWordWrap(True)
                neden_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                neden_lbl.setStyleSheet("""
                    color: #e0e0e0; font-size: 13px; padding: 12px;
                    background-color: #16213e; border: 1px solid #3a3a5c;
                    border-radius: 8px;
                """)
                scroll_layout.addWidget(neden_lbl)

            # Urun Ozellikleri tablosu
            urun_oz = getattr(ai_result, 'urun_ozellikleri', [])
            if urun_oz:
                scroll_layout.addWidget(self._section_header(f"URUN OZELLIKLERI ({len(urun_oz)} adet)"))
                for oz in urun_oz:
                    ozellik = oz.get('ozellik', '')
                    deger = oz.get('deger', '')
                    scroll_layout.addWidget(self._labeled_box(ozellik, deger, "#8e8ea0"))

            # Kullanim Alanlari
            kullanim = getattr(ai_result, 'kullanim_alanlari', '')
            if kullanim:
                scroll_layout.addWidget(self._labeled_box(
                    "Kullanim Alanlari", kullanim, "#B388FF"
                ))

            # Long-tail Sorgular
            uzun_kuyruk = getattr(ai_result, 'uzun_kuyruk_sorgular', [])
            if uzun_kuyruk:
                scroll_layout.addWidget(self._section_header(f"LONG-TAIL SORGULAR ({len(uzun_kuyruk)} adet)"))
                sorgu_text = "\n".join([f"  • {s}" for s in uzun_kuyruk])
                sorgu_lbl = QLabel(sorgu_text)
                sorgu_lbl.setWordWrap(True)
                sorgu_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                sorgu_lbl.setStyleSheet("color: #c0c0c0; font-size: 12px; padding: 8px; background-color: #0f0f23; border-radius: 6px;")
                scroll_layout.addWidget(sorgu_lbl)

            # Aciklama
            scroll_layout.addWidget(self._section_header("ACIKLAMA (GEO + E-E-A-T + FAQ Iceren)"))
            aciklama_lbl = QLabel(ai_result.aciklama)
            aciklama_lbl.setWordWrap(True)
            aciklama_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            aciklama_lbl.setStyleSheet("""
                color: #e0e0e0; font-size: 13px; padding: 12px;
                background-color: #16213e; border: 1px solid #3a3a5c;
                border-radius: 8px; line-height: 1.6;
            """)
            scroll_layout.addWidget(aciklama_lbl)

            # GEO SSS
            if ai_result.geo_sss:
                scroll_layout.addWidget(self._section_header(f"GEO SSS ({len(ai_result.geo_sss)} soru)"))
                for i, sss in enumerate(ai_result.geo_sss):
                    soru = sss.get('soru', '')
                    cevap = sss.get('cevap', '')
                    faq_widget = QWidget()
                    faq_layout = QVBoxLayout(faq_widget)
                    faq_layout.setContentsMargins(12, 8, 12, 8)
                    faq_widget.setStyleSheet("""
                        background-color: #16213e; border: 1px solid #3a3a5c;
                        border-radius: 8px;
                    """)
                    q_lbl = QLabel(f"S{i+1}: {soru}")
                    q_lbl.setWordWrap(True)
                    q_lbl.setStyleSheet("color: #00BFA6; font-weight: bold; font-size: 13px; border: none;")
                    q_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    faq_layout.addWidget(q_lbl)
                    a_lbl = QLabel(f"{cevap}")
                    a_lbl.setWordWrap(True)
                    a_lbl.setStyleSheet("color: #c0c0c0; font-size: 12px; border: none;")
                    a_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    faq_layout.addWidget(a_lbl)
                    scroll_layout.addWidget(faq_widget)
        else:
            scroll_layout.addWidget(self._section_header("AI ANALIZ SONUCU"))
            no_result = QLabel("Bu urun henuz analiz edilmedi.")
            no_result.setStyleSheet("color: #8e8ea0; font-size: 14px; padding: 20px;")
            no_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(no_result)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Kapat butonu
        btn_close = QPushButton("Kapat")
        btn_close.setFixedHeight(40)
        btn_close.clicked.connect(self.close)
        close_layout = QHBoxLayout()
        close_layout.setContentsMargins(20, 8, 20, 12)
        close_layout.addStretch()
        close_layout.addWidget(btn_close)
        close_layout.addStretch()
        layout.addLayout(close_layout)

    def _section_header(self, text: str, accent: bool = False) -> QLabel:
        """Bolum basligi olusturur."""
        lbl = QLabel(text)
        color = "#00D4B8" if accent else "#00BFA6"
        lbl.setStyleSheet(f"""
            color: {color}; font-size: 15px; font-weight: bold;
            padding: 6px 0; border-bottom: 1px solid #3a3a5c;
            margin-top: 8px;
        """)
        return lbl

    def _info_card(self, pairs: list) -> QWidget:
        """Anahtar-deger ciflerini kart formatinda gosterir."""
        card = QWidget()
        card.setStyleSheet("""
            background-color: #16213e; border: 1px solid #3a3a5c;
            border-radius: 8px; padding: 8px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)
        for key, val in pairs:
            row = QHBoxLayout()
            k_lbl = QLabel(f"{key}:")
            k_lbl.setStyleSheet("color: #8e8ea0; font-weight: bold; min-width: 130px; border: none;")
            k_lbl.setFixedWidth(140)
            v_lbl = QLabel(str(val))
            v_lbl.setWordWrap(True)
            v_lbl.setStyleSheet("color: #e0e0e0; border: none;")
            v_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(k_lbl)
            row.addWidget(v_lbl, 1)
            card_layout.addLayout(row)
        return card

    def _labeled_box(self, label: str, value: str, color: str) -> QWidget:
        """Etiketli bir metin kutusu olusturur."""
        box = QWidget()
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        box_layout.addWidget(lbl)
        val = QLabel(value)
        val.setWordWrap(True)
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        val.setStyleSheet("""
            color: #e0e0e0; font-size: 13px; padding: 10px;
            background-color: #16213e; border: 1px solid #3a3a5c;
            border-radius: 6px;
        """)
        box_layout.addWidget(val)
        return box


# ──────────────── ANA PENCERE ────────────────

class MainWindow(QMainWindow):
    """Ticimax AI Manager ana penceresi."""

    def __init__(self):
        """MainWindow olusturucusu."""
        super().__init__()
        self.setWindowTitle("Ticimax AI Manager")
        self.setMinimumSize(1200, 800)

        # Durum degiskenleri
        self.ticimax_url = ""
        self.ticimax_ws = ""
        self.gemini_key = ""
        self.raw_urunler = []          # API'den gelen ham veriler
        self.ai_results = {}           # {satir_index: ProductAIContent}
        self.create_results = []       # Create mode sonuclari
        self.session_state = SessionState()  # Checkpoint sistemi

        # Stacked widget: login -> main
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Login paneli
        self.login_panel = LoginPanel()
        self.login_panel.connect_requested.connect(self._handle_connect)
        self.stack.addWidget(self.login_panel)

        # Ana icerik paneli
        self.main_panel = QWidget()
        self._build_main_ui()
        self.stack.addWidget(self.main_panel)

        self.stack.setCurrentIndex(0)

    # ─── ANA ARAYUZ KURULUMU ───

    def _build_main_ui(self):
        """Ana calisma ekranini olusturur."""
        root_layout = QVBoxLayout(self.main_panel)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        # Ust bar: Firma bilgisi + Cikis
        top_bar = QHBoxLayout()
        self.lbl_firma = QLabel("Firma: -")
        self.lbl_firma.setStyleSheet("font-size: 14px; color: #00BFA6; font-weight: bold;")
        top_bar.addWidget(self.lbl_firma)
        top_bar.addStretch()
        btn_logout = QPushButton("Oturumu Kapat")
        btn_logout.setObjectName("dangerBtn")
        btn_logout.setFixedWidth(160)
        btn_logout.clicked.connect(self._logout)
        top_bar.addWidget(btn_logout)
        root_layout.addLayout(top_bar)

        # Splitter: Sol (Tabs) + Sag (Log)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol panel: Tab'lar
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self._build_update_tab()
        self._build_create_tab()
        left_layout.addWidget(self.tabs)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m urun islendi")
        left_layout.addWidget(self.progress)

        splitter.addWidget(left_panel)

        # Sag panel: Log
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        lbl_log = QLabel("Islem Logu")
        lbl_log.setStyleSheet("font-weight: bold; color: #00BFA6;")
        right_layout.addWidget(lbl_log)
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        right_layout.addWidget(self.log_panel)
        splitter.addWidget(right_panel)

        splitter.setSizes([800, 400])
        root_layout.addWidget(splitter)

    # ─── UPDATE MODE TAB ───

    def _build_update_tab(self):
        """Bulut modunu (mevcut urunleri guncelle) olusturur."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        # Butonlar
        btn_row = QHBoxLayout()
        self.btn_fetch = QPushButton("Urunleri Cek")
        self.btn_fetch.clicked.connect(self._fetch_products)
        btn_row.addWidget(self.btn_fetch)

        self.chk_select_all = QCheckBox("Tumunu Sec")
        self.chk_select_all.setEnabled(False)
        self.chk_select_all.stateChanged.connect(self._toggle_select_all)
        btn_row.addWidget(self.chk_select_all)
        
        # Araya biraz bosluk
        btn_row.addStretch()

        self.btn_analyze = QPushButton("AI ile Analiz Et")
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self._analyze_products)
        btn_row.addWidget(self.btn_analyze)

        self.btn_export = QPushButton("Excel'e Aktar")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_excel)
        btn_row.addWidget(self.btn_export)

        layout.addLayout(btn_row)

        # Tablo
        self.update_table = QTableWidget()
        self.update_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.update_table.setAlternatingRowColors(True)
        self.update_table.horizontalHeader().setStretchLastSection(True)
        self.update_table.doubleClicked.connect(self._on_table_double_click)
        layout.addWidget(self.update_table)

        self.tabs.addTab(tab, "Update Mode (Bulut)")

    # ─── CREATE MODE TAB ───

    def _build_create_tab(self):
        """Yerel modu (sifirdan urun karti olustur) olusturur."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        btn_row = QHBoxLayout()
        self.btn_select_folder = QPushButton("Klasor Sec")
        self.btn_select_folder.clicked.connect(self._select_folder)
        btn_row.addWidget(self.btn_select_folder)

        self.lbl_folder = QLabel("Klasor secilmedi")
        self.lbl_folder.setStyleSheet("color: #8e8ea0;")
        btn_row.addWidget(self.lbl_folder)
        btn_row.addStretch()

        self.btn_create_analyze = QPushButton("Sifirdan Analiz Et")
        self.btn_create_analyze.setEnabled(False)
        self.btn_create_analyze.clicked.connect(self._analyze_create_mode)
        btn_row.addWidget(self.btn_create_analyze)

        self.btn_create_export = QPushButton("Excel'e Aktar")
        self.btn_create_export.setEnabled(False)
        self.btn_create_export.clicked.connect(self._export_create_excel)
        btn_row.addWidget(self.btn_create_export)

        layout.addLayout(btn_row)

        # Tablo
        self.create_table = QTableWidget()
        self.create_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.create_table.setAlternatingRowColors(True)
        self.create_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.create_table)

        self.tabs.addTab(tab, "Create Mode (Yerel)")

    # ─── BAGLANTI & LOGIN ───

    def _handle_connect(self, url: str, ws: str, gem: str):
        """Login ekranindan gelen baglanti istegi."""
        self.ticimax_url = url
        self.ticimax_ws = ws
        self.gemini_key = gem

        # Hizlica WSDL baglantisinmi kontrol et
        try:
            TicimaxClient(base_url=url, uye_kodu=ws)
            # Basarili
            domain = url.split("/Servis")[0].replace("https://", "").replace("http://", "")
            self.lbl_firma.setText(f"Firma: {domain}")
            self._log(f"Basariyla baglandi: {domain}")
            self.stack.setCurrentIndex(1)
        except Exception as e:
            self.login_panel.lbl_status.setText(f"Baglanti hatasi: {e}")
            self.login_panel.reset_button()

    def _logout(self):
        """Oturumu kapatir ve giris ekranina doner."""
        self.ticimax_url = ""
        self.ticimax_ws = ""
        self.gemini_key = ""
        self.raw_urunler = []
        self.ai_results = {}
        self.update_table.setRowCount(0)
        self.create_table.setRowCount(0)
        self.log_panel.clear()
        self.progress.setValue(0)
        self.login_panel.reset_button()
        self.stack.setCurrentIndex(0)
        self.btn_analyze.setEnabled(False)
        self.btn_export.setEnabled(False)

    # ─── LOG ───

    def _log(self, msg: str):
        """Log paneline mesaj ekler."""
        self.log_panel.append(msg)
        self.log_panel.verticalScrollBar().setValue(
            self.log_panel.verticalScrollBar().maximum()
        )

    # ─── UPDATE MODE: URUN CEKME ───

    def _on_table_double_click(self, index):
        """Tabloda bir satira cift tiklandiginda detay dialog'unu acar."""
        row = index.row()
        if row < 0 or row >= len(self.raw_urunler):
            return

        urun = self.raw_urunler[row]
        ai_result = self.ai_results.get(row, None)

        # Gorsel URL'lerini cikar
        resim_urls = []
        resimler = get_field(urun, 'Resimler')
        if resimler:
            string_list = get_field(resimler, 'string')
            if string_list and isinstance(string_list, list):
                resim_urls = [url for url in string_list if url]
        if not resim_urls:
            tek_url = get_field(urun, 'ResimURL')
            if tek_url:
                resim_urls = [tek_url]

        dialog = ProductDetailDialog(
            parent=self,
            row_idx=row,
            urun_data=urun,
            ai_result=ai_result,
            resim_urls=resim_urls
        )
        dialog.exec()

    def _fetch_products(self):
        """Ticimax'ten urunleri arka planda ceker."""
        self.btn_fetch.setEnabled(False)
        self._log("Urun listesi cekiliyor...")

        self._ticimax_worker = TicimaxWorker(self.ticimax_url, self.ticimax_ws)
        self._ticimax_worker.finished.connect(self._on_products_fetched)
        self._ticimax_worker.error.connect(self._on_fetch_error)
        self._ticimax_worker.log.connect(self._log)
        self._ticimax_worker.start()

    def _on_products_fetched(self, urunler: list):
        """Urunler basariyla cekildikten sonra tabloyu doldurur."""
        self.raw_urunler = urunler
        self.btn_fetch.setEnabled(True)

        if not urunler:
            self._log("[UYARI] Hic urun bulunamadi.")
            return

        # Tablo kolonlarini ayarla
        headers = ["Sec", "ID", "Stok Kodu", "Urun Adi", "Marka", "Gorsel",
                    "AI Urun Adi", "AI SEO Baslik", "AI SEO Aciklama", "Durum"]
        self.update_table.setColumnCount(len(headers))
        self.update_table.setHorizontalHeaderLabels(headers)
        self.update_table.setRowCount(len(urunler))

        for row, urun in enumerate(urunler):
            # Checkbox
            chk = QCheckBox()
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.update_table.setCellWidget(row, 0, chk_widget)

            urun_id = get_field(urun, 'ID') or get_field(urun, 'UrunKartiID')
            stok = get_field(urun, 'StokKodu')
            adi = get_field(urun, 'UrunAdi') or get_field(urun, 'Tanim')
            marka = get_field(urun, 'Marka', '')

            # TUM resim URL'lerini cikart
            resim_urls = []
            resimler = get_field(urun, 'Resimler')
            if resimler:
                string_list = get_field(resimler, 'string')
                if string_list and isinstance(string_list, list):
                    resim_urls = [url for url in string_list if url]
            
            # Fallback: tekli ResimURL alani
            if not resim_urls:
                tek_url = get_field(urun, 'ResimURL')
                if tek_url:
                    resim_urls = [tek_url]
            
            # Gorsel bilgisini tabloda goster
            gorsel_bilgi = f"{len(resim_urls)} gorsel" if resim_urls else "Gorsel yok"

            self.update_table.setItem(row, 1, QTableWidgetItem(str(urun_id)))
            self.update_table.setItem(row, 2, QTableWidgetItem(str(stok)))
            self.update_table.setItem(row, 3, QTableWidgetItem(str(adi)))
            self.update_table.setItem(row, 4, QTableWidgetItem(str(marka)))
            self.update_table.setItem(row, 5, QTableWidgetItem(gorsel_bilgi))
            self.update_table.setItem(row, 6, QTableWidgetItem(""))
            self.update_table.setItem(row, 7, QTableWidgetItem(""))
            self.update_table.setItem(row, 8, QTableWidgetItem(""))
            status_item = QTableWidgetItem("Bekliyor")
            status_item.setForeground(QColor("#8e8ea0"))
            self.update_table.setItem(row, 9, status_item)

        self.update_table.resizeColumnsToContents()
        self.btn_analyze.setEnabled(True)
        self.chk_select_all.setEnabled(True)
        self.progress.setMaximum(len(urunler))
        self.progress.setValue(0)
        self.progress.setFormat(f"0 / {len(urunler)} urun islendi")
        self._log(f"{len(urunler)} urun tabloya yuklendi. Istediginiz urunleri secip 'AI ile Analiz Et' butonuna basabilirsiniz.")

    def _on_fetch_error(self, msg: str):
        """Urun cekme hatasi."""
        self.btn_fetch.setEnabled(True)
        self._log(f"[HATA] Urun cekme basarisiz: {msg}")

    def _toggle_select_all(self, state):
        """Tum checkbox'lari isaretler veya kaldirir."""
        is_checked = (state == Qt.CheckState.Checked.value) or (state == 2)
        for row in range(self.update_table.rowCount()):
            chk_widget = self.update_table.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk:
                    chk.setChecked(is_checked)

    # ─── UPDATE MODE: AI ANALIZ ───

    def _analyze_products(self):
        """Secili urunleri Gemini ile analiz eder (tum gorselleriyle)."""
        # Analiz edilecek urunleri hazirla
        urunler_data = []
        for row in range(self.update_table.rowCount()):
            # Sadece secili (checkbox isaretli) olanlari analiz et
            chk_widget = self.update_table.cellWidget(row, 0)
            if not chk_widget:
                continue
            chk = chk_widget.findChild(QCheckBox)
            if not chk or not chk.isChecked():
                continue

            urun = self.raw_urunler[row]
            marka = self.update_table.item(row, 4).text() if self.update_table.item(row, 4) else ""
            urun_adi = self.update_table.item(row, 3).text() if self.update_table.item(row, 3) else ""
            
            # Tum gorsel URL'lerini urun objesinden cikar
            resim_urls = []
            resimler = get_field(urun, 'Resimler')
            if resimler:
                string_list = get_field(resimler, 'string')
                if string_list and isinstance(string_list, list):
                    resim_urls = [url for url in string_list if url]
            if not resim_urls:
                tek_url = get_field(urun, 'ResimURL')
                if tek_url:
                    resim_urls = [tek_url]
            
            urunler_data.append({
                'raw': urun,
                'resim_urls': resim_urls,
                'resim_url': resim_urls[0] if resim_urls else '',
                'marka': marka,
                'urun_adi': urun_adi,
                'row_idx': row
            })

        if not urunler_data:
            self._log("[UYARI] Analiz edilecek urun secilmedi. Lutfen tablodan urun secin.")
            QMessageBox.warning(self, "Uyari", "Lutfen analiz edilecek urunleri 'Sec' kutucuklarindan isaretleyin.")
            return

        self.btn_analyze.setEnabled(False)
        self.btn_fetch.setEnabled(False)
        self.progress.setMaximum(len(urunler_data))
        self.progress.setValue(0)

        # Session checkpoint baslat
        indices = list(range(len(urunler_data)))
        domain = self.ticimax_url.split("/Servis")[0].replace("https://", "").replace("http://", "")
        self.session_state.init_session(domain, indices)

        domain_url = self.ticimax_url.split("/Servis")[0]
        self._vision_worker = VisionWorker(
            self.gemini_key, urunler_data, domain_url, 
            session_state=self.session_state
        )
        self._vision_worker.progress.connect(lambda cur, tot: self.progress.setValue(cur))
        self._vision_worker.product_done.connect(self._on_product_analyzed)
        self._vision_worker.error.connect(self._on_product_error)
        self._vision_worker.finished.connect(self._on_all_analyzed)
        self._vision_worker.log.connect(self._log)
        self._vision_worker.start()

    def _on_product_analyzed(self, idx: int, ai_result):
        """Tek bir urun basariyla analiz edildikten sonra tabloyu gunceller."""
        self.ai_results[idx] = ai_result
        self.update_table.setItem(idx, 6, QTableWidgetItem(ai_result.urun_adi))
        self.update_table.setItem(idx, 7, QTableWidgetItem(ai_result.seo_baslik))
        self.update_table.setItem(idx, 8, QTableWidgetItem(ai_result.seo_aciklama))
        status = QTableWidgetItem("Analiz Edildi")
        status.setForeground(QColor("#00BFA6"))
        self.update_table.setItem(idx, 9, status)
        # Checkbox'i otomatik isaretle
        chk_widget = self.update_table.cellWidget(idx, 0)
        if chk_widget:
            chk = chk_widget.findChild(QCheckBox)
            if chk:
                chk.setChecked(True)

    def _on_product_error(self, idx: int, msg: str):
        """Tek bir urunun analizi basarisiz oldu."""
        status = QTableWidgetItem("Hata")
        status.setForeground(QColor("#e74c3c"))
        self.update_table.setItem(idx, 9, status)

    def _on_all_analyzed(self):
        """Tum analizler tamamlandi."""
        self.btn_analyze.setEnabled(True)
        self.btn_fetch.setEnabled(True)
        self.btn_export.setEnabled(True)
        self._log(f"Analiz tamamlandi! {len(self.ai_results)} urun basariyla islendi.")
        # Session temizle
        self.session_state.clear()

    # ─── UPDATE MODE: EXCEL EXPORT ───

    def _export_excel(self):
        """Kiyaslama ve Ticimax sablonunu Excel'e aktarir."""
        if not self.ai_results:
            self._log("[UYARI] Henuz analiz yapilmamis, export edilecek veri yok.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Excel Kaydet", "ticimax_seo_dokumu.xlsx", "Excel (*.xlsx)")
        if not path:
            return

        TEMPLATE_COLS = ['URUNKARTIID', 'URUNID', 'STOKKODU', 'VARYASYONKODU', 'BARKOD', 'URUNADI', 'ONYAZI', 'ACIKLAMA', 'PUANDEGER', 'PUANYUZDE', 'MARKA', 'TEDARIKCI', 'MAKSTAKSITSAYISI', 'BREADCRUMBKAT', 'KATEGORILER', 'SATISBIRIMI', 'VITRIN', 'YENIURUN', 'FIRSATURUNU', 'FBSTOREGOSTER', 'SEO_SAYFABASLIK', 'SEO_ANAHTARKELIME', 'SEO_SAYFAACIKLAMA', 'UCRETSIZKARGO', 'STOKADEDI', 'ALISFIYATI', 'SATISFIYATI', 'INDIRIMLIFIYAT', 'UYETIPIFIYAT1', 'UYETIPIFIYAT2', 'UYETIPIFIYAT3', 'UYETIPIFIYAT4', 'UYETIPIFIYAT5', 'KDVORANI', 'KDVDAHIL', 'PARABIRIMI', 'KUR', 'KARGOAGIRLIGI', 'KARGOAGIRLIGIYURTDISI', 'URUNGENISLIK', 'URUNDERINLIK', 'URUNYUKSEKLIK', 'URUNAGIRLIGI', 'KARGOUCRETI', 'URUNAKTIF', 'VARYASYON', 'TAHMINITESLIMSURESIGOSTER', 'URUNADEDIMINIMUMDEGER', 'URUNADEDIVARSAYILANDEGER', 'URUNADEDIARTISKADEMESI', 'GTIPKODU', 'OZELALAN1', 'OZELALAN2', 'OZELALAN3', 'OZELALAN4', 'OZELALAN5', 'VERGIISTISNAKODU', 'YEMEKKARTIODEMEYASAKLILISTESI', 'MOBILBEDENTABLOSUAKTIF', 'MOBILBEDENTABLOSUICERIK', 'PAZARYERIAKTIFLISTESI']

        upload_rows = []

        for idx, ai_result in self.ai_results.items():
            urun = self.raw_urunler[idx]

            # Zenginlestirilmis HTML aciklama olustur
            ai_aciklama_full = ai_result.aciklama

            # GEO Ozet blogu
            geo_ozet = getattr(ai_result, 'geo_ozet', '')
            if geo_ozet:
                ai_aciklama_full += f'<div class="geo-ozet" style="background:#f8f9fa;border-left:4px solid #00BFA6;padding:12px;margin:16px 0;"><p><em>{geo_ozet}</em></p></div>'

            # Urun ozellikleri tablosu
            urun_ozellikleri = getattr(ai_result, 'urun_ozellikleri', [])
            if urun_ozellikleri:
                ai_aciklama_full += '<h3>Teknik Ozellikler</h3><table style="width:100%;border-collapse:collapse;">'
                for oz in urun_ozellikleri:
                    ozellik = oz.get('ozellik', '')
                    deger = oz.get('deger', '')
                    ai_aciklama_full += f'<tr><td style="padding:8px;border:1px solid #ddd;font-weight:bold;width:35%;">{ozellik}</td><td style="padding:8px;border:1px solid #ddd;">{deger}</td></tr>'
                ai_aciklama_full += '</table>'

            # SSS bolumu (FAQ Schema uyumlu)
            ai_aciklama_full += '<br/><h3>Sikca Sorulan Sorular</h3>'
            for q_dict in ai_result.geo_sss:
                q = q_dict.get('soru', '')
                a = q_dict.get('cevap', '')
                ai_aciklama_full += f'<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question"><h4 itemprop="name">{q}</h4><div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer"><p itemprop="text">{a}</p></div></div>'

            # JSON-LD FAQ Schema
            faq_entries = []
            for q_dict in ai_result.geo_sss:
                q = q_dict.get('soru', '')
                a = q_dict.get('cevap', '')
                faq_entries.append(f'{{"@type":"Question","name":"{q}","acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}')
            faq_schema = '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + ','.join(faq_entries) + ']}'
            ai_aciklama_full += f'<script type="application/ld+json">{faq_schema}</script>'

            # JSON-LD Product Schema
            stok_kodu_val = get_field(urun, 'StokKodu') or ''
            marka_val = get_field(urun, 'Marka') or ''
            fiyat_val = get_field(urun, 'SatisFiyati') or '0'
            para_birimi_val = get_field(urun, 'ParaBirimi') or 'TRY'
            stok_adedi_val = get_field(urun, 'StokAdedi')
            availability = "InStock" if stok_adedi_val and float(stok_adedi_val) > 0 else "OutOfStock"
            
            product_schema = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": str(ai_result.urun_adi).replace('"', '\\"'),
                "description": str(ai_result.seo_aciklama).replace('"', '\\"'),
                "sku": str(stok_kodu_val),
                "brand": {
                    "@type": "Brand",
                    "name": str(marka_val).replace('"', '\\"')
                },
                "offers": {
                    "@type": "Offer",
                    "url": "",
                    "priceCurrency": str(para_birimi_val),
                    "price": str(fiyat_val),
                    "itemCondition": "https://schema.org/NewCondition",
                    "availability": f"https://schema.org/{availability}"
                }
            }
            import json
            prod_schema_str = json.dumps(product_schema, ensure_ascii=False)
            ai_aciklama_full += f'<script type="application/ld+json">{prod_schema_str}</script>'

            urun_karti_id = get_field(urun, 'ID') or get_field(urun, 'UrunKartiID')
            
            # Varyasyonlari Kontrol Et
            varyasyonlar = get_field(urun, 'Varyasyonlar')
            var_list = []
            if varyasyonlar:
                v_data = get_field(varyasyonlar, 'Varyasyon')
                if v_data and isinstance(v_data, list):
                    var_list = v_data
                elif v_data:
                    var_list = [v_data]
                    
            # Eger varyasyon yoksa kendisini bos sozluk gibi isle
            if not var_list:
                var_list = [{}]

            for var in var_list:
                row_upload = {}
                for col in TEMPLATE_COLS:
                    # 1) Once varyasyon spesifik degerine bak
                    val = get_field(var, col)
                    # 2) Eger varyasyonda yoksa, ana urunden cek
                    if val == "":
                        val = get_field(urun, col)
                        
                    # 3) AI kolonlarini ve ID'leri Override Et
                    if col.upper() == 'URUNADI':
                        val = ai_result.urun_adi
                    elif col.upper() == 'ONYAZI':
                        val = ai_result.onyazi
                    elif col.upper() == 'ACIKLAMA':
                        val = ai_aciklama_full
                    elif col.upper() == 'SEO_SAYFABASLIK':
                        val = ai_result.seo_baslik
                    elif col.upper() == 'SEO_SAYFAACIKLAMA':
                        val = ai_result.seo_aciklama
                    elif col.upper() == 'SEO_ANAHTARKELIME':
                        val = ai_result.seo_anahtarkelime
                    elif col.upper() == 'URUNKARTIID':
                        val = urun_karti_id
                    elif col.upper() == 'URUNID':
                        var_id = get_field(var, 'ID')
                        val = var_id if var_id else urun_karti_id
                    # NOT: OZELALAN1-5 su an bos birakilmistir.

                    # Bos degerleri ve "None" metinlerini temizle
                    field_str = str(val) if val is not None else ""
                    if field_str == "None":
                        field_str = ""
                        
                    row_upload[col] = field_str
                upload_rows.append(row_upload)

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            pd.DataFrame(upload_rows).to_excel(writer, sheet_name="Worksheet", index=False)

        self._log(f"Excel basariyla kaydedildi: {path}")

    # ─── CREATE MODE ───

    def _select_folder(self):
        """Yerel klasor secme dialog'u."""
        folder = QFileDialog.getExistingDirectory(self, "Urun Gorselleri Klasoru Secin")
        if folder:
            self.lbl_folder.setText(folder)
            self.lbl_folder.setStyleSheet("color: #00BFA6;")
            self._selected_folder = folder
            self.btn_create_analyze.setEnabled(True)

    def _analyze_create_mode(self):
        """Secilen klasordeki gorselleri Gemini ile analiz eder."""
        folder = getattr(self, '_selected_folder', None)
        if not folder:
            return

        self.btn_create_analyze.setEnabled(False)
        self.create_results = []

        # Tablo hazirla
        headers = ["Klasor / Dosya", "AI Urun Adi", "AI SEO Baslik", "AI SEO Aciklama", "AI Onyazi"]
        self.create_table.setColumnCount(len(headers))
        self.create_table.setHorizontalHeaderLabels(headers)
        self.create_table.setRowCount(0)

        self._create_worker = CreateModeWorker(self.gemini_key, folder)
        self._create_worker.progress.connect(lambda c, t: self.progress.setValue(c))
        self._create_worker.product_done.connect(self._on_create_product_done)
        self._create_worker.finished.connect(self._on_create_finished)
        self._create_worker.log.connect(self._log)

        # Progress bar maximum'u belirleme -> worker basladiktan sonra gelecek
        self.progress.setMaximum(0)  # indeterminate
        self._create_worker.start()

    def _on_create_product_done(self, idx: int, klasor_adi: str, ai_result):
        """Yerel modda tek bir gorsel analiz edildikten sonra."""
        row = self.create_table.rowCount()
        self.create_table.insertRow(row)
        self.create_table.setItem(row, 0, QTableWidgetItem(klasor_adi))
        self.create_table.setItem(row, 1, QTableWidgetItem(ai_result.urun_adi))
        self.create_table.setItem(row, 2, QTableWidgetItem(ai_result.seo_baslik))
        self.create_table.setItem(row, 3, QTableWidgetItem(ai_result.seo_aciklama))
        self.create_table.setItem(row, 4, QTableWidgetItem(ai_result.onyazi))
        self.create_results.append({'klasor': klasor_adi, 'ai': ai_result})

    def _on_create_finished(self):
        """Create mode analizi tamamlandi."""
        self.btn_create_analyze.setEnabled(True)
        self.btn_create_export.setEnabled(True)
        self.progress.setMaximum(1)
        self.progress.setValue(1)
        self._log(f"Yerel analiz tamamlandi! {len(self.create_results)} urun islendi.")

    def _export_create_excel(self):
        """Create mode sonuclarini Excel'e aktarir."""
        if not self.create_results:
            self._log("[UYARI] Export edilecek veri yok.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Excel Kaydet", "yeni_urunler.xlsx", "Excel (*.xlsx)")
        if not path:
            return

        rows = []
        for item in self.create_results:
            ai = item['ai']
            # Zenginlestirilmis aciklama
            ai_aciklama_full = ai.aciklama
            geo_ozet = getattr(ai, 'geo_ozet', '')
            if geo_ozet:
                ai_aciklama_full += f'<div class="geo-ozet" style="background:#f8f9fa;border-left:4px solid #00BFA6;padding:12px;margin:16px 0;"><p><em>{geo_ozet}</em></p></div>'
            urun_oz = getattr(ai, 'urun_ozellikleri', [])
            if urun_oz:
                ai_aciklama_full += '<h3>Teknik Ozellikler</h3><table style="width:100%;border-collapse:collapse;">'
                for oz in urun_oz:
                    ai_aciklama_full += f'<tr><td style="padding:8px;border:1px solid #ddd;font-weight:bold;width:35%;">{oz.get("ozellik","")}</td><td style="padding:8px;border:1px solid #ddd;">{oz.get("deger","")}</td></tr>'
                ai_aciklama_full += '</table>'
            ai_aciklama_full += '<br/><h3>Sikca Sorulan Sorular</h3>'
            for q_dict in ai.geo_sss:
                q = q_dict.get('soru', '')
                a = q_dict.get('cevap', '')
                ai_aciklama_full += f'<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question"><h4 itemprop="name">{q}</h4><div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer"><p itemprop="text">{a}</p></div></div>'
            
            # JSON-LD FAQ Schema
            faq_entries = []
            for q_dict in ai.geo_sss:
                q = q_dict.get('soru', '')
                a = q_dict.get('cevap', '')
                faq_entries.append(f'{{"@type":"Question","name":"{q}","acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}')
            faq_schema = '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + ','.join(faq_entries) + ']}'
            ai_aciklama_full += f'<script type="application/ld+json">{faq_schema}</script>'

            # JSON-LD Product Schema (Create Mode)
            product_schema = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": str(ai.urun_adi).replace('"', '\\"'),
                "description": str(ai.seo_aciklama).replace('"', '\\"'),
                "sku": str(item['klasor']),
                "offers": {
                    "@type": "Offer",
                    "url": "",
                    "priceCurrency": "TRY",
                    "price": "0",
                    "itemCondition": "https://schema.org/NewCondition",
                    "availability": "https://schema.org/InStock"
                }
            }
            import json
            prod_schema_str = json.dumps(product_schema, ensure_ascii=False)
            ai_aciklama_full += f'<script type="application/ld+json">{prod_schema_str}</script>'
            uzun_kuyruk = getattr(ai, 'uzun_kuyruk_sorgular', [])
            rows.append({
                "STOKKODU": item['klasor'],
                "URUNADI": ai.urun_adi,
                "ONYAZI": ai.onyazi,
                "ACIKLAMA": ai_aciklama_full,
                "SEO_SAYFABASLIK": ai.seo_baslik,
                "SEO_SAYFAACIKLAMA": ai.seo_aciklama,
                "SEO_ANAHTARKELIME": ai.seo_anahtarkelime,
                "OZELALAN1_GORSEL_ALT_TEXT": getattr(ai, 'gorsel_alt_text', ''),
                "OZELALAN2_ODAK_KELIME": getattr(ai, 'hedef_anahtar_kelime', ''),
                "OZELALAN3_GEO_OZET": getattr(ai, 'geo_ozet', ''),
                "OZELALAN4_KULLANIM": getattr(ai, 'kullanim_alanlari', ''),
                "OZELALAN5_LONG_TAIL": ', '.join(uzun_kuyruk) if uzun_kuyruk else '',
            })

        pd.DataFrame(rows).to_excel(path, index=False)
        self._log(f"Yeni urunler Excel'e kaydedildi: {path}")

    # ─── TRIPLE-CHECK ONAY SISTEMI ───

    def _triple_check_and_send(self):
        """
        Uc asamali onay mekanizmasi:
        Asama 1: Tablodaki checkbox'larin kontrol edilmesi.
        Asama 2: Pop-up onay penceresi.
        Asama 3: Kullanicinin 'ONAYLIYORUM' yazmasi veya 4 haneli kod girmesi.
        """
        # ASAMA 1: Secili urunleri say
        secili_indexler = []
        for row in range(self.update_table.rowCount()):
            chk_widget = self.update_table.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.isChecked() and row in self.ai_results:
                    secili_indexler.append(row)

        if not secili_indexler:
            QMessageBox.warning(self, "Uyari", "Hic urun secilmedi! Oncelikle tablodaki onay kutucuklarini isaretleyin.")
            return

        # ASAMA 2: Pop-up
        yanit = QMessageBox.question(
            self,
            "Ticimax Gonderim Onayi",
            f"{len(secili_indexler)} adet urun Ticimax'e gonderilecek.\nBu islem geri alinamaz. Emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if yanit != QMessageBox.StandardButton.Yes:
            self._log("Gonderim kullanici tarafindan iptal edildi (Asama 2).")
            return

        # ASAMA 3: Kullanicidan metin onay veya guvenlik kodu
        kod = str(random.randint(1000, 9999))
        text, ok = QInputDialog.getText(
            self,
            "Son Guvenlik Kontrolu",
            f"Son adim: Asagidaki kodu girin: {kod}\n\n(ya da 'ONAYLIYORUM' yazin)",
        )
        if not ok:
            self._log("Gonderim kullanici tarafindan iptal edildi (Asama 3).")
            return
        if text.strip() != kod and text.strip().upper() != "ONAYLIYORUM":
            QMessageBox.critical(self, "Guvenlik Hatasi",
                                 "Girilen kod veya onay metni uyusmuyor. Islem iptal edildi.")
            self._log("[IPTAL] Guvenlik kodu eslesmedi.")
            return

        # ONAY GECTI — Gonderim buraya gelecek
        self._log(f"[ONAY GECTI] {len(secili_indexler)} urun gonderime hazir. (Save Urun henuz devre disi)")
        QMessageBox.information(self, "Basarili",
                                f"{len(secili_indexler)} urun onaylandi.\nSave Urun modulu aktif oldugunda gonderim baslatilacaktir.")
