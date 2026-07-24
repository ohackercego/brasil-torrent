import json
import os
from app_paths import resource_path


LANGUAGE_NAMES = {
    "pt-BR": "Português (Brasil)",
    "en-US": "English (US)",
}


class I18n:
    """Gerenciador de internacionalização inspirado no WinZapp."""

    def __init__(self, language: str = "pt-BR"):
        self._language = language
        self._strings: dict = {}
        self.load(language)

    def load(self, language: str):
        """Carrega o arquivo de idioma."""
        self._language = language
        path = resource_path(os.path.join("languages", f"{language}.json"))
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._strings = json.load(f)
            except Exception:
                self._strings = {}
        else:
            self._strings = {}

    def t(self, key: str, **kwargs) -> str:
        """Retorna a string traduzida para a chave."""
        val = self._strings.get(key)
        if val is None:
            return key
        if kwargs:
            try:
                return val.format(**kwargs)
            except KeyError:
                return val
        return val


i18n = I18n()
