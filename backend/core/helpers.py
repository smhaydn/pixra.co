"""
Ticimax AI Manager — Yardimci Fonksiyonlar ve Hata Toleransi Araclari
get_field, download_image, firma yonetimi ve fault-tolerant utility'ler.
"""

import os
import json
import time
import requests
import functools
from typing import Optional, Callable, Any


# ──────────────── SABITLER ────────────────

FIRMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firms.json")
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_state.json")


# ──────────────── TEMEL YARDIMCILAR ────────────────

def get_field(obj, field_name: str, default=""):
    """Zeep/SOAP objesi icinde hem attribute hem de dict key arar (harf duyarli ve duyarsiz)."""
    # 1. Exact match (attribute)
    if hasattr(obj, field_name):
        val = getattr(obj, field_name)
        return val if val is not None else default
    
    # 2. Exact match (dict)
    if isinstance(obj, dict) and field_name in obj:
        val = obj.get(field_name)
        return val if val is not None else default
    
    # 3. Case-insensitive and underscore-ignoring match for attributes/dicts
    target = field_name.lower().replace("_", "")
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower().replace("_", "") == target:
                return v if v is not None else default
    else:
        for attr in dir(obj):
            if not attr.startswith('_') and attr.lower().replace("_", "") == target:
                val = getattr(obj, attr)
                return val if val is not None else default
                
    return default


def download_image(url: str, save_path: str) -> bool:
    """Belirtilen URL'den gorseli indirir. Bos dosyalari reddeder."""
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        if os.path.getsize(save_path) == 0:
            return False
        return True
    except Exception:
        return False


def safe_file_cleanup(file_paths: list):
    """Gecici dosyalari guvenli sekilde temizler. Hata firlatmaz."""
    for fp in file_paths:
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception:
                pass


# ──────────────── FIRMA YONETIMI ────────────────

def load_saved_firms() -> list:
    """Kaydedilmis firma bilgilerini JSON dosyasindan okur."""
    if os.path.exists(FIRMS_FILE):
        try:
            with open(FIRMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_firms_to_file(firms: list):
    """Firma bilgilerini JSON dosyasina yazar."""
    with open(FIRMS_FILE, "w", encoding="utf-8") as f:
        json.dump(firms, f, ensure_ascii=False, indent=2)


# ──────────────── HATA TOLERANSI (FAULT-TOLERANT) ────────────────

def retry_with_backoff(max_retries: int = 3, base_delay: float = 5.0, 
                       backoff_factor: float = 3.0, 
                       retryable_exceptions: tuple = (Exception,)):
    """
    Exponential Backoff ile otomatik yeniden deneme dekoratoru.
    
    Calisma sekli:
        1. deneme -> Aninda
        2. deneme -> base_delay saniye bekle (5s)
        3. deneme -> base_delay * backoff_factor saniye bekle (15s)
    Tum denemeler basarisiz -> Orijinal hatayi firlatir.
    
    Args:
        max_retries (int): Maksimum deneme sayisi.
        base_delay (float): Ilk bekleme suresi (saniye).
        backoff_factor (float): Her denemede bekleme carpani.
        retryable_exceptions (tuple): Yeniden denenmesi gereken hata tipleri.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        # 429 rate limit hatalari icin ekstra bekleme
                        err_str = str(e)
                        if "429" in err_str or "quota" in err_str.lower():
                            delay = delay * 2
                        time.sleep(delay)
                    else:
                        raise last_exception
        return wrapper
    return decorator


class SessionState:
    """
    Analiz ilerlemesini JSON dosyasina kaydeden checkpoint sistemi.
    Uygulama cokerse veya kapatilirsa, kaldigi yerden devam edebilir.
    
    Kayit formati:
        {
            "firma": "www.example.com",
            "timestamp": "2026-04-14T23:00:00",
            "total": 58,
            "processed": [0, 1, 2, 3],
            "failed": [4],
            "pending": [5, 6, 7, ...],
            "results": { "0": {...}, "1": {...} }
        }
    """

    def __init__(self, session_path: str = None):
        """SessionState olusturucusu."""
        self.path = session_path or SESSION_FILE
        self.data = {
            "firma": "",
            "timestamp": "",
            "total": 0,
            "processed": [],
            "failed": [],
            "pending": [],
            "results": {}
        }

    def init_session(self, firma: str, total_indices: list):
        """Yeni bir analiz oturumu baslatir."""
        self.data = {
            "firma": firma,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total": len(total_indices),
            "processed": [],
            "failed": [],
            "pending": list(total_indices),
            "results": {}
        }
        self._save()

    def mark_processed(self, idx: int, result_summary: dict = None):
        """Bir urunu basariyla islenmis olarak isaretler."""
        if idx in self.data["pending"]:
            self.data["pending"].remove(idx)
        if idx not in self.data["processed"]:
            self.data["processed"].append(idx)
        if result_summary:
            self.data["results"][str(idx)] = result_summary
        self._save()

    def mark_failed(self, idx: int, error_msg: str = ""):
        """Bir urunu basarisiz olarak isaretler."""
        if idx in self.data["pending"]:
            self.data["pending"].remove(idx)
        if idx not in self.data["failed"]:
            self.data["failed"].append(idx)
        self.data["results"][str(idx)] = {"error": error_msg}
        self._save()

    def get_pending(self) -> list:
        """Henuz islenmemis urun index'lerini dondurur."""
        return list(self.data.get("pending", []))

    def has_pending_session(self) -> bool:
        """Devam ettirilebilecek bir oturum var mi kontrol eder."""
        if not os.path.exists(self.path):
            return False
        try:
            self.load()
            return len(self.data.get("pending", [])) > 0
        except Exception:
            return False

    def load(self):
        """Mevcut session dosyasini yukler."""
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def clear(self):
        """Oturum dosyasini temizler/siler."""
        self.data = {"firma": "", "timestamp": "", "total": 0, 
                     "processed": [], "failed": [], "pending": [], "results": {}}
        if os.path.exists(self.path):
            try:
                os.remove(self.path)
            except Exception:
                pass

    def get_summary(self) -> str:
        """Oturum durumunun ozetini dondurur."""
        p = len(self.data.get("processed", []))
        f = len(self.data.get("failed", []))
        pend = len(self.data.get("pending", []))
        firma = self.data.get("firma", "?")
        ts = self.data.get("timestamp", "?")
        return f"Firma: {firma} | Tarih: {ts} | Tamamlanan: {p} | Hata: {f} | Bekleyen: {pend}"

    def _save(self):
        """Durumu JSON dosyasina yazar."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
