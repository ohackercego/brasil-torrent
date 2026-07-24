"""Testes unitários para core/i18n.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.i18n import I18n, LANGUAGE_NAMES


class TestI18nInitialization(unittest.TestCase):
    """Testes para criação e configuração do I18n."""

    def test_default_language(self):
        i18n = I18n()
        self.assertEqual(i18n._language, "pt-BR")

    def test_custom_language(self):
        i18n = I18n("en-US")
        self.assertEqual(i18n._language, "en-US")

    def test_language_names_dict(self):
        self.assertIn("pt-BR", LANGUAGE_NAMES)
        self.assertIn("en-US", LANGUAGE_NAMES)
        self.assertEqual(LANGUAGE_NAMES["pt-BR"], "Portugu\u00eas (Brasil)")
        self.assertEqual(LANGUAGE_NAMES["en-US"], "English (US)")


class TestI18nTranslations(unittest.TestCase):
    """Testes para carregamento e uso de traduções."""

    def setUp(self):
        self.pt = I18n("pt-BR")
        self.en = I18n("en-US")

    def test_pt_br_loaded(self):
        self.assertEqual(self.pt.t("app_name"), "Brasil Torrent")
        self.assertEqual(self.pt.t("nav_transfers"), "Transfer\u00eancias")
        self.assertEqual(self.pt.t("state_baixando"), "Baixando")
        self.assertEqual(self.pt.t("settings_title"), "Configura\u00e7\u00f5es")

    def test_en_us_loaded(self):
        self.assertEqual(self.en.t("app_name"), "Brasil Torrent")
        self.assertEqual(self.en.t("nav_transfers"), "Transfers")
        self.assertEqual(self.en.t("state_baixando"), "Downloading")
        self.assertEqual(self.en.t("settings_title"), "Settings")

    def test_missing_key_returns_key(self):
        self.assertEqual(self.pt.t("chave_inexistente"), "chave_inexistente")
        self.assertEqual(self.en.t("nonexistent_key"), "nonexistent_key")

    def test_empty_key(self):
        self.assertEqual(self.pt.t(""), "")

    def test_format_kwargs(self):
        # Chave que não existe com kwargs — retorna a chave
        result = self.pt.t("hello_{name}", name="World")
        self.assertEqual(result, "hello_{name}")

    def test_load_switch_language(self):
        self.pt.load("en-US")
        self.assertEqual(self.pt._language, "en-US")
        self.assertEqual(self.pt.t("nav_transfers"), "Transfers")


class TestI18nStateTranslations(unittest.TestCase):
    """Testes para chaves de estado de torrent."""

    def setUp(self):
        self.pt = I18n("pt-BR")
        self.en = I18n("en-US")

    def test_all_states_pt_br(self):
        states = [
            ("parado", "parado"),
            ("pausado", "pausado"),
            ("aguardando_verificacao", "aguardando_verificacao"),
            ("verificando", "verificando"),
            ("obtendo_metadados", "obtendo_metadados"),
            ("baixando", "baixando"),
            ("finalizado", "finalizado"),
            ("distribuindo", "distribuindo"),
            ("alocando", "alocando"),
            ("verificando_retomada", "verificando_retomada"),
            ("desconhecido", "desconhecido"),
        ]
        for state_key in [s[0] for s in states]:
            self.assertNotEqual(
                self.pt.t(f"state_{state_key}"), f"state_{state_key}",
                f"Chave state_{state_key} não encontrada em pt-BR",
            )

    def test_all_states_en_us(self):
        states = [
            "parado",
            "pausado",
            "aguardando_verificacao",
            "verificando",
            "obtendo_metadados",
            "baixando",
            "finalizado",
            "distribuindo",
            "alocando",
            "verificando_retomada",
            "desconhecido",
        ]
        for state_key in states:
            self.assertNotEqual(
                self.en.t(f"state_{state_key}"), f"state_{state_key}",
                f"Chave state_{state_key} não encontrada em en-US",
            )


class TestI18nMenuTranslations(unittest.TestCase):
    """Testes para chaves de menu."""

    def test_menu_keys_pt_br(self):
        i18n = I18n("pt-BR")
        self.assertIn("Arquivo", i18n.t("menu_file"))
        self.assertIn("Exibir", i18n.t("menu_view"))
        self.assertIn("Ferramentas", i18n.t("menu_tools"))
        self.assertIn("Ajuda", i18n.t("menu_help"))

    def test_menu_keys_en_us(self):
        i18n = I18n("en-US")
        self.assertIn("File", i18n.t("menu_file"))
        self.assertIn("View", i18n.t("menu_view"))
        self.assertIn("Tools", i18n.t("menu_tools"))
        self.assertIn("Help", i18n.t("menu_help"))


if __name__ == "__main__":
    unittest.main()
