import unittest
import json
import tempfile
import time
from helpers.file_lock import FileLock


class TestFileLock(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmpfile = self.tmpdir.name + '/file.json'
        with open(self.tmpfile, 'w') as fp:
            json.dump({"data": 42}, fp)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        return super().tearDown()

    def test_file_lock_read(self):
        fl = FileLock(self.tmpfile)
        self.assertEqual(fl.get_file_name(), self.tmpfile)
        self.assertTrue(fl.open(timeout=0))
        self.assertFalse(fl.is_exclusive())
        content = json.load(fl.get_fp())
        self.assertEqual(content.get("data"), 42)

        # concurrent read is ok
        fl2 = FileLock(self.tmpfile)
        self.assertTrue(fl2.open(timeout=0))
        content = json.load(fl2.get_fp())
        self.assertEqual(content.get("data"), 42)
        self.assertTrue(fl2.close())

        # concurrent write fails
        self.assertFalse(fl2.open(exclusive=True, timeout=0))
        self.assertIsNone(fl2.get_fp())
        self.assertFalse(fl2.close())

        self.assertTrue(fl.close())
        self.assertIsNone(fl.get_fp())

    def test_file_lock_write(self):
        fl = FileLock(self.tmpfile)
        self.assertEqual(fl.get_file_name(), self.tmpfile)
        self.assertTrue(fl.open(exclusive=True, timeout=0))
        self.assertTrue(fl.is_exclusive())
        json.dump({"data": 54}, fl.get_fp())

        # concurrent read fails
        fl2 = FileLock(self.tmpfile)
        self.assertFalse(fl2.open(timeout=0))
        self.assertIsNone(fl2.get_fp())
        self.assertFalse(fl2.close())

        self.assertTrue(fl.close())
        self.assertIsNone(fl.get_fp())

        with open(self.tmpfile, "r") as fp:
            content = json.load(fp)
            self.assertEqual(content.get("data"), 54)

    def test_file_lock_timeout(self):
        fl = FileLock(self.tmpfile)
        self.assertEqual(fl.get_file_name(), self.tmpfile)
        self.assertTrue(fl.open(exclusive=True, timeout=1))
        self.assertTrue(fl.is_exclusive())

        # concurrent read fails
        fl2 = FileLock(self.tmpfile)
        start_ts = time.time()
        self.assertFalse(fl2.open(timeout=1))
        duration = time.time() - start_ts
        self.assertTrue(duration > 0.5)
        self.assertTrue(duration < 2.0)
        self.assertIsNone(fl2.get_fp())
        self.assertFalse(fl2.close())

        self.assertTrue(fl.close())
        self.assertIsNone(fl.get_fp())


if __name__ == '__main__':
    unittest.main()
