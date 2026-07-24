"""Testes unitários para core/utils.py."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.utils import (
    format_size,
    format_speed,
    format_duration,
    format_eta,
    format_percent,
    format_ratio,
    is_magnet_link,
    is_torrent_file,
    sanitize_filename,
    bytes_to_int,
)


class TestFormatSize(unittest.TestCase):
    """Testes para format_size."""

    def test_zero_bytes(self):
        self.assertEqual(format_size(0), "0 B")

    def test_bytes(self):
        self.assertEqual(format_size(1), "1.00 B")
        self.assertEqual(format_size(500), "500.00 B")

    def test_kilobytes(self):
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1536), "1.50 KB")
        self.assertEqual(format_size(1024 * 10), "10.00 KB")

    def test_megabytes(self):
        self.assertEqual(format_size(1024 ** 2), "1.00 MB")
        self.assertEqual(format_size(1024 ** 2 * 2), "2.00 MB")
        self.assertEqual(format_size(1024 ** 2 * 5 + 500 * 1024), "5.49 MB")

    def test_gigabytes(self):
        self.assertEqual(format_size(1024 ** 3), "1.00 GB")
        self.assertEqual(format_size(1024 ** 3 * 15), "15.00 GB")

    def test_terabytes(self):
        self.assertEqual(format_size(1024 ** 4), "1.00 TB")

    def test_negative(self):
        self.assertEqual(format_size(-1), "0 B")


class TestFormatSpeed(unittest.TestCase):
    """Testes para format_speed."""

    def test_zero(self):
        self.assertEqual(format_speed(0), "0 B/s")

    def test_bytes_per_sec(self):
        self.assertEqual(format_speed(500), "500.00 B/s")

    def test_kilobytes_per_sec(self):
        self.assertEqual(format_speed(1024), "1.00 KB/s")

    def test_megabytes_per_sec(self):
        self.assertEqual(format_speed(1024 * 1024), "1.00 MB/s")
        self.assertEqual(format_speed(5 * 1024 * 1024), "5.00 MB/s")

    def test_negative(self):
        self.assertEqual(format_speed(-100), "0 B/s")


class TestFormatDuration(unittest.TestCase):
    """Testes para format_duration."""

    def test_seconds_only(self):
        self.assertEqual(format_duration(0), "0s")
        self.assertEqual(format_duration(30), "30s")
        self.assertEqual(format_duration(59), "59s")

    def test_minutes(self):
        self.assertEqual(format_duration(60), "1m 00s")
        self.assertEqual(format_duration(90), "1m 30s")
        self.assertEqual(format_duration(3600 - 1), "59m 59s")

    def test_hours(self):
        self.assertEqual(format_duration(3600), "1h 00m 00s")
        self.assertEqual(format_duration(3661), "1h 01m 01s")
        self.assertEqual(format_duration(7200), "2h 00m 00s")
        self.assertEqual(format_duration(3661 + 7200), "3h 01m 01s")

    def test_negative(self):
        self.assertEqual(format_duration(-1), "0s")
        self.assertEqual(format_duration(-100), "0s")


class TestFormatEta(unittest.TestCase):
    """Testes para format_eta."""

    def test_normal_eta(self):
        self.assertEqual(format_eta(3600), "1h 00m 00s")
        self.assertEqual(format_eta(90), "1m 30s")
        self.assertEqual(format_eta(0), "0s")

    def test_indefinite(self):
        # libtorrent usa 8640000 para ETA indefinido
        self.assertEqual(format_eta(8640000), "\u2014")

    def test_negative(self):
        self.assertEqual(format_eta(-1), "\u2014")


class TestFormatPercent(unittest.TestCase):
    """Testes para format_percent."""

    def test_zero(self):
        self.assertEqual(format_percent(0.0), "0.0%")

    def test_half(self):
        self.assertEqual(format_percent(0.5), "50.0%")

    def test_full(self):
        self.assertEqual(format_percent(1.0), "100.0%")

    def test_precision(self):
        self.assertEqual(format_percent(0.756), "75.6%")
        self.assertEqual(format_percent(0.3333), "33.3%")

    def test_above_hundred(self):
        self.assertEqual(format_percent(1.5), "150.0%")


class TestFormatRatio(unittest.TestCase):
    """Testes para format_ratio."""

    def test_zero_download(self):
        self.assertEqual(format_ratio(100, 0), "\u2014")

    def test_zero_both(self):
        self.assertEqual(format_ratio(0, 0), "\u2014")

    def test_normal_ratio(self):
        self.assertEqual(format_ratio(500000, 1000000), "0.50")

    def test_equal(self):
        self.assertEqual(format_ratio(1000, 1000), "1.00")

    def test_high_ratio(self):
        self.assertEqual(format_ratio(2000000, 1000000), "2.00")

    def test_no_upload(self):
        self.assertEqual(format_ratio(0, 1000000), "0.00")


class TestIsMagnetLink(unittest.TestCase):
    """Testes para is_magnet_link."""

    def test_valid_magnet(self):
        self.assertTrue(is_magnet_link("magnet:?xt=urn:btih:abc123def456"))
        self.assertTrue(is_magnet_link("magnet:?xt=urn:btih:abc&dn=file"))

    def test_with_whitespace(self):
        self.assertTrue(is_magnet_link("  magnet:?xt=urn:btih:abc  "))

    def test_invalid(self):
        self.assertFalse(is_magnet_link(""))
        self.assertFalse(is_magnet_link("http://example.com"))
        self.assertFalse(is_magnet_link("not a magnet"))
        self.assertFalse(is_magnet_link("magnet"))


class TestIsTorrentFile(unittest.TestCase):
    """Testes para is_torrent_file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_valid_torrent(self):
        path = os.path.join(self.tmpdir, "test.torrent")
        with open(path, "w") as f:
            f.write("dummy")
        self.assertTrue(is_torrent_file(path))

    def test_non_existent(self):
        self.assertFalse(is_torrent_file(os.path.join(self.tmpdir, "nope.torrent")))

    def test_wrong_extension(self):
        path = os.path.join(self.tmpdir, "test.txt")
        with open(path, "w") as f:
            f.write("dummy")
        self.assertFalse(is_torrent_file(path))

    def test_no_extension(self):
        path = os.path.join(self.tmpdir, "test")
        with open(path, "w") as f:
            f.write("dummy")
        self.assertFalse(is_torrent_file(path))

    def test_empty_string(self):
        self.assertFalse(is_torrent_file(""))

    def test_case_insensitive_extension(self):
        # No Windows .TORRENT também deve funcionar
        path = os.path.join(self.tmpdir, "test.TORRENT")
        with open(path, "w") as f:
            f.write("dummy")
        self.assertTrue(is_torrent_file(path))


class TestSanitizeFilename(unittest.TestCase):
    """Testes para sanitize_filename."""

    def test_clean_name(self):
        self.assertEqual(sanitize_filename("ubuntu-22.04.iso"), "ubuntu-22.04.iso")

    def test_with_spaces(self):
        self.assertEqual(sanitize_filename("my file.txt"), "my file.txt")

    def test_with_invalid_chars(self):
        self.assertEqual(sanitize_filename('file<>:"/\\|?*.txt'), "file_________.txt")

    def test_all_invalid(self):
        self.assertEqual(sanitize_filename('<>:"/\\|?*'), "_________")

    def test_empty(self):
        self.assertEqual(sanitize_filename(""), "")


class TestBytesToInt(unittest.TestCase):
    """Testes para bytes_to_int."""

    def test_int(self):
        self.assertEqual(bytes_to_int(42), 42)

    def test_float(self):
        self.assertEqual(bytes_to_int(42.7), 42)

    def test_string_digits(self):
        self.assertEqual(bytes_to_int("42"), 42)

    def test_string_invalid(self):
        self.assertEqual(bytes_to_int("abc"), 0)

    def test_none(self):
        self.assertEqual(bytes_to_int(None), 0)

    def test_zero(self):
        self.assertEqual(bytes_to_int(0), 0)


if __name__ == "__main__":
    unittest.main()
