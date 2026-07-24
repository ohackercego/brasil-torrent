"""Testes unitários para app_paths.py e version.py."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_paths import resource_path, data_path, log_path, download_path
from version import __version__, __app_name__, __author__, __description__


class TestVersion(unittest.TestCase):
    """Testes para constants de versão."""

    def test_version_format(self):
        parts = __version__.split(".")
        self.assertEqual(len(parts), 3)
        for p in parts:
            self.assertTrue(p.isdigit())

    def test_app_name(self):
        self.assertEqual(__app_name__, "Brasil Torrent")

    def test_author_not_empty(self):
        self.assertTrue(len(__author__) > 0)

    def test_description_not_empty(self):
        self.assertTrue(len(__description__) > 0)


class TestResourcePath(unittest.TestCase):
    """Testes para resource_path."""

    def test_returns_absolute_path(self):
        path = resource_path("test.txt")
        self.assertTrue(os.path.isabs(path))

    def test_contains_client_dir(self):
        path = resource_path("languages")
        self.assertTrue("client" in path or "client" in os.path.normpath(path))

    def test_relative_preserved(self):
        path = resource_path("languages/pt-BR.json")
        self.assertTrue(path.endswith("pt-BR.json"))


class TestDataPath(unittest.TestCase):
    """Testes para data_path."""

    def test_returns_absolute(self):
        path = data_path()
        self.assertTrue(os.path.isabs(path))

    def test_with_relative(self):
        path = data_path("subdir")
        self.assertTrue(path.endswith("subdir"))

    def test_creates_directory(self):
        path = data_path()
        self.assertTrue(os.path.isdir(path))


class TestLogPath(unittest.TestCase):
    """Testes para log_path."""

    def test_creates_directory(self):
        path = log_path()
        self.assertTrue(os.path.isdir(path))
        self.assertTrue("logs" in path.lower() or "logs" in path)


class TestDownloadPath(unittest.TestCase):
    """Testes para download_path."""

    def test_creates_directory(self):
        path = download_path()
        self.assertTrue(os.path.isdir(path))

    def test_with_relative(self):
        path = download_path("ubuntu")
        self.assertTrue(path.endswith("ubuntu"))

    def test_default_exists(self):
        path = download_path()
        self.assertTrue(os.path.isdir(path))


if __name__ == "__main__":
    unittest.main()
