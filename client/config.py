import os
import json
from app_paths import data_path


_CONFIG_FILE = os.path.join(data_path(), "settings.json")


def _load_defaults() -> dict:
    return {
        "connection": {
            "max_upload_rate": 0,       # 0 = ilimitado (bytes/s)
            "max_download_rate": 0,     # 0 = ilimitado (bytes/s)
            "max_connections": 200,
            "listen_port": 6881,
            "enable_dht": True,
            "enable_lsd": True,
            "enable_upnp": True,
            "enable_natpmp": True,
            "proxy_type": "none",       # none, socks5, http
            "proxy_host": "",
            "proxy_port": 0,
            "proxy_username": "",
            "proxy_password": "",
        },
        "general": {
            "language": "pt-BR",
            "download_path": "",
            "max_active_downloads": 5,
            "max_active_uploads": 5,
            "min_ratio": 1.0,
            "min_seed_time": 3600,      # segundos
            "auto_start": False,
            "minimize_to_tray": True,
            "notifications_enabled": True,
            "confirm_exit": True,
            "terms_accepted": False,    # Termos de uso aceitos?
            "progress_announce_interval": 10,  # Anunciar progresso a cada N%
        },
        "appearance": {
            "show_speed_limit_icon": True,
            "show_tray_icon": True,
        },
        "privacy": {
            "anonymous_mode": False,
        }
    }


class Config(dict):
    """Gerenciamento de configurações com persistência em JSON."""

    def __init__(self):
        super().__init__()
        self._file = _CONFIG_FILE
        self._dirty = False
        self.load()

    def load(self):
        """Carrega configurações do disco, mesclando com defaults."""
        defaults = _load_defaults()
        if os.path.isfile(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._deep_merge(defaults, saved)
            except Exception:
                pass
        self.update(defaults)

    def save(self):
        """Persiste configurações no disco."""
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self, f, indent=4, ensure_ascii=False)
            self._dirty = False
        except Exception:
            pass

    def _deep_merge(self, base: dict, override: dict):
        """Mescla override em base recursivamente."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_setting(self, *keys, default=None):
        """Acessa uma configuração aninhada seguramente."""
        current = self
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current


settings = Config()
