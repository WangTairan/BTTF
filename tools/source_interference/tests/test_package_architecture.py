from __future__ import annotations

import unittest
from pathlib import Path


class PackageArchitectureTests(unittest.TestCase):
    def test_language_modules_do_not_depend_on_each_other(self) -> None:
        package_root = Path(__file__).parents[1] / "src" / "readability_data"
        java_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (package_root / "java_degradation").rglob("*.py")
        )
        python_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (package_root / "python_degradation").rglob("*.py")
        )
        self.assertNotIn("python_degradation", java_source)
        self.assertNotIn("java_degradation", python_source)


if __name__ == "__main__":
    unittest.main()
