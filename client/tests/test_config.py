"""Testes unitários para config.py.

Abordagem: em vez de patchear data_path (que não funciona com reload),
manipulamos o _file de cada instância Config diretamente.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config


class TestConfig(unittest.TestCase):
    """Testes para a classe Config."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "settings.json")
        self.config = Config()
        self.config._file = self.config_path
        # Recarrega do arquivo vazio (garante defaults)
        self.config.load()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_values_connection(self):
        conn = self.config.get_setting("connection")
        self.assertEqual(conn["max_upload_rate"], 0)
        self.assertEqual(conn["max_download_rate"], 0)
        self.assertEqual(conn["max_connections"], 200)
        self.assertEqual(conn["listen_port"], 6881)
        self.assertTrue(conn["enable_dht"])
        self.assertTrue(conn["enable_lsd"])
        self.assertTrue(conn["enable_upnp"])
        self.assertTrue(conn["enable_natpmp"])
        self.assertEqual(conn["proxy_type"], "none")

    def test_default_values_general(self):
        general = self.config.get_setting("general")
        self.assertEqual(general["language"], "pt-BR")
        self.assertEqual(general["download_path"], "")
        self.assertEqual(general["max_active_downloads"], 5)
        self.assertEqual(general["max_active_uploads"], 5)
        self.assertEqual(general["min_ratio"], 1.0)
        self.assertEqual(general["min_seed_time"], 3600)
        self.assertFalse(general["auto_start"])
        self.assertTrue(general["minimize_to_tray"])
        self.assertTrue(general["notifications_enabled"])
        self.assertTrue(general["confirm_exit"])

    def test_default_values_privacy(self):
        priv = self.config.get_setting("privacy")
        self.assertFalse(priv["anonymous_mode"])

    def test_get_setting_nested(self):
        self.assertEqual(
            self.config.get_setting("connection", "listen_port", default=6881),
            6881,
        )

    def test_get_setting_missing_returns_default(self):
        self.assertEqual(
            self.config.get_setting("nonexistent", default=42), 42
        )

    def test_get_setting_deep_missing_returns_default(self):
        self.assertEqual(
            self.config.get_setting("connection", "nonexistent", default="fallback"),
            "fallback",
        )

    def test_set_and_get(self):
        self.config["general"]["language"] = "en-US"
        self.assertEqual(
            self.config.get_setting("general", "language"), "en-US"
        )

    def test_save_and_load(self):
        """Salva, depois cria nova instância e verifica que carregou."""
        self.config["connection"]["max_connections"] = 300
        self.config.save()

        new_config = Config()
        new_config._file = self.config_path
        # O construtor já carregou, mas recarregamos para garantir
        new_config.load()
        self.assertEqual(
            new_config.get_setting("connection", "max_connections"), 300
        )
        # Outros defaults devem permanecer
        self.assertEqual(
            new_config.get_setting("connection", "listen_port"), 6881
        )

    def test_deep_merge_override(self):
        """Verifica que deep_merge não destrói defaults com parciais."""
        self.config._deep_merge(
            self.config, {"connection": {"max_connections": 500}}
        )
        # O valor específico foi sobrescrito
        self.assertEqual(
            self.config.get_setting("connection", "max_connections"), 500
        )
        # Outros valores devem permanecer inalterados
        self.assertEqual(
            self.config.get_setting("connection", "listen_port"), 6881
        )
        self.assertEqual(
            self.config.get_setting("general", "language"), "pt-BR"
        )

    def test_deep_merge_new_keys(self):
        """Chaves novas devem ser adicionadas."""
        self.config._deep_merge(
            self.config, {"nova_secao": {"chave": "valor"}}
        )
        self.assertEqual(
            self.config.get_setting("nova_secao", "chave"), "valor"
        )


class TestConfigPersistence(unittest.TestCase):
    """Testes específicos para persistência em disco."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "settings.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_creates_file(self):
        cfg = Config()
        cfg._file = self.config_path
        cfg.save()
        self.assertTrue(os.path.isfile(self.config_path))

    def test_save_valid_json(self):
        cfg = Config()
        cfg._file = self.config_path
        cfg["general"]["language"] = "en-US"
        cfg.save()

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["general"]["language"], "en-US")
        # Deve ter todas as seções
        self.assertIn("connection", data)
        self.assertIn("privacy", data)

    def test_corrupted_file_falls_back_to_defaults(self):
        """JSON corrompido no disco deve carregar defaults sem crash."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{corrupted json")

        cfg = Config()
        cfg._file = self.config_path
        cfg.load()
        self.assertEqual(
            cfg.get_setting("connection", "max_connections"), 200
        )
        self.assertEqual(
            cfg.get_setting("general", "language"), "pt-BR"
        )

    def test_load_preserves_saved_values(self):
        """Salva, recarrega e verifica todos os valores."""
        cfg1 = Config()
        cfg1._file = self.config_path
        cfg1["connection"]["max_connections"] = 150
        cfg1["connection"]["enable_dht"] = False
        cfg1["general"]["language"] = "en-US"
        cfg1["general"]["auto_start"] = True
        cfg1.save()

        cfg2 = Config()
        cfg2._file = self.config_path
        cfg2.load()
        self.assertEqual(cfg2.get_setting("connection", "max_connections"), 150)
        self.assertFalse(cfg2.get_setting("connection", "enable_dht"))
        self.assertEqual(cfg2.get_setting("general", "language"), "en-US")
        self.assertTrue(cfg2.get_setting("general", "auto_start"))

    def test_empty_file_uses_defaults(self):
        """Arquivo vazio deve carregar defaults."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("")

        cfg = Config()
        cfg._file = self.config_path
        cfg.load()
        self.assertEqual(
            cfg.get_setting("connection", "max_connections"), 200
        )


if __name__ == "__main__":
    unittest.main()
