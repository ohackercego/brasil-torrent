"""Testes unitários para TorrentEntry (core/torrent_engine.py)."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.torrent_engine import TorrentEntry


class TestTorrentEntry(unittest.TestCase):
    """Testes para o dataclass TorrentEntry."""

    def setUp(self):
        self.entry = TorrentEntry(
            info_hash="abc123def456",
            name="Ubuntu 22.04.iso",
            save_path=r"C:\Downloads",
        )

    def test_creation_minimal(self):
        self.assertEqual(self.entry.info_hash, "abc123def456")
        self.assertEqual(self.entry.name, "Ubuntu 22.04.iso")
        self.assertEqual(self.entry.save_path, r"C:\Downloads")
        self.assertEqual(self.entry.size, 0)
        self.assertEqual(self.entry.progress, 0.0)
        self.assertEqual(self.entry.download_rate, 0)
        self.assertEqual(self.entry.upload_rate, 0)
        self.assertEqual(self.entry.state, 0)
        self.assertEqual(self.entry.eta, -1)  # desconhecido
        self.assertFalse(self.entry.paused)
        self.assertFalse(self.entry.stopped)
        self.assertFalse(self.entry.is_magnet)
        self.assertFalse(self.entry.is_finished)
        self.assertEqual(self.entry.error, "")

    def test_full_creation(self):
        now = time.time()
        entry = TorrentEntry(
            info_hash="xyz789",
            name="test.torrent",
            save_path=r"D:\torrents",
            size=1024 ** 3,
            progress=0.75,
            download_rate=500000,
            upload_rate=100000,
            total_download=800 * 1024 * 1024,
            total_upload=400 * 1024 * 1024,
            num_peers=5,
            num_seeds=10,
            total_peers=20,
            total_seeds=50,
            state=3,
            eta=3600,
            added_date=now,
            completed_date=0,
            paused=False,
            is_magnet=False,
            is_finished=False,
        )
        self.assertEqual(entry.info_hash, "xyz789")
        self.assertEqual(entry.size, 1073741824)
        self.assertEqual(entry.progress, 0.75)
        self.assertEqual(entry.download_rate, 500000)
        self.assertEqual(entry.upload_rate, 100000)
        self.assertEqual(entry.num_peers, 5)
        self.assertEqual(entry.num_seeds, 10)
        self.assertEqual(entry.state, 3)
        self.assertEqual(entry.eta, 3600)

    def test_magnet_entry(self):
        entry = TorrentEntry(
            info_hash="magnet123",
            name="Obtendo metadados...",
            save_path=r"C:\Downloads",
            is_magnet=True,
            added_date=time.time(),
        )
        self.assertTrue(entry.is_magnet)
        self.assertEqual(entry.name, "Obtendo metadados...")

    def test_finished_entry(self):
        entry = TorrentEntry(
            info_hash="fin123",
            name="Finished.iso",
            save_path=r"C:\Downloads",
            progress=1.0,
            is_finished=True,
            completed_date=time.time(),
        )
        self.assertTrue(entry.is_finished)
        self.assertEqual(entry.progress, 1.0)

    def test_paused_entry(self):
        entry = TorrentEntry(
            info_hash="pause123",
            name="Paused.torrent",
            save_path=r"C:\Downloads",
            paused=True,
        )
        self.assertTrue(entry.paused)

    def test_state_str_downloading(self):
        import libtorrent as lt
        entry = TorrentEntry(
            info_hash="st1",
            name="test",
            save_path=".",
            state=lt.torrent_status.states.downloading,
        )
        self.assertEqual(entry.state_str, "state_baixando")

    def test_state_str_seeding(self):
        import libtorrent as lt
        entry = TorrentEntry(
            info_hash="st2",
            name="test",
            save_path=".",
            state=lt.torrent_status.states.seeding,
        )
        self.assertEqual(entry.state_str, "state_distribuindo")

    def test_state_str_finished(self):
        import libtorrent as lt
        entry = TorrentEntry(
            info_hash="st3",
            name="test",
            save_path=".",
            state=lt.torrent_status.states.finished,
        )
        self.assertEqual(entry.state_str, "state_finalizado")

    def test_state_str_unknown(self):
        entry = TorrentEntry(
            info_hash="st4",
            name="test",
            save_path=".",
            state=999,  # valor inválido
        )
        self.assertEqual(entry.state_str, "state_desconhecido")

    def test_state_str_paused(self):
        entry = TorrentEntry(
            info_hash="st5",
            name="test",
            save_path=".",
            state=3,
            paused=True,
        )
        self.assertEqual(entry.state_str, "state_pausado")

    def test_state_str_stopped(self):
        entry = TorrentEntry(
            info_hash="st6",
            name="test",
            save_path=".",
            state=3,
            stopped=True,
        )
        self.assertEqual(entry.state_str, "state_parado")

    def test_empty_error(self):
        self.assertEqual(self.entry.error, "")

    def test_with_error(self):
        entry = TorrentEntry(
            info_hash="err1",
            name="Broken",
            save_path=".",
            error="Connection timeout",
        )
        self.assertEqual(entry.error, "Connection timeout")


if __name__ == "__main__":
    unittest.main()
