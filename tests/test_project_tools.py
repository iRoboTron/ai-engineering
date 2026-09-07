import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class InstallerTests(unittest.TestCase):
    def test_install_idempotent_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, dest = base / "source", base / "dest"
            source.mkdir()
            (source / "sample.py").write_text("print('safe')\n")
            install = module("install_labs").install
            self.assertEqual(install(source, dest), 1)
            self.assertEqual(install(source, dest), 0)
            (dest / "sample.py").write_text("my work")
            (source / "new.py").write_text("new")
            with self.assertRaises(ValueError):
                install(source, dest)
            self.assertEqual((dest / "sample.py").read_text(), "my work")
            self.assertFalse((dest / "new.py").exists())

    def test_private_artifacts_not_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            source.mkdir()
            (source / ".env").write_text("SECRET=not-for-export")
            (source / ".local").mkdir()
            (source / ".local/secret").write_text("private")
            self.assertEqual(module("install_labs").install(source, base / "dest"), 0)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, dest, outside = [base / n for n in ("source", "dest", "outside")]
            for p in (source / "nested", dest, outside):
                p.mkdir(parents=True)
            (source / "nested/file.py").write_text("safe")
            (dest / "nested").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                module("install_labs").install(source, dest)
            self.assertFalse((outside / "file.py").exists())


if __name__ == "__main__":
    unittest.main()
