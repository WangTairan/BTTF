import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from readability_data.java_degradation.pipeline import construct_interference_dataset
from readability_data.java_degradation.registry import interference_registry

SOURCE = b"""/** docs */
public class Readable {
  int calculateTotal(int itemCount) {
    int resultValue = itemCount + 7;
    return resultValue;
  }
}
"""


class InterferencePipelineTest(unittest.TestCase):
    def test_interferences_are_separate_direct_source_variants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "Readable.java").write_bytes(SOURCE)
            (source / "Second.java").write_bytes(SOURCE.replace(b"Readable", b"Second"))
            output = root / "interferences"

            provenance = construct_interference_dataset(source, output, seed=7)
            rows = [
                json.loads(line)
                for line in (output / "manifest.jsonl").read_text().splitlines()
            ]
            plugin_count = len(interference_registry())
            self.assertEqual(provenance["interference_count"], plugin_count)
            self.assertEqual(len(rows), 2 * (plugin_count + 1))
            for base_id in {row["base_sample_id"] for row in rows}:
                variants = [row for row in rows if row["base_sample_id"] == base_id]
                original = next(row for row in variants if row["order"] == 0)
                transformed = [row for row in variants if row["order"] > 0]
                self.assertEqual(
                    {row["parent_variant_id"] for row in transformed},
                    {original["variant_id"]},
                )
                self.assertTrue(
                    all(len(row["applied_interferences"]) == 1 for row in transformed)
                )
            self.assertTrue((output / "source-original").is_dir())
            self.assertTrue((output / "comments" / "remove-comments").is_dir())
            self.assertTrue((output / "identifiers" / "mislead-identifiers").is_dir())
            report = (output / "obfuscation-report.html").read_text(encoding="utf-8")
            self.assertIn("Java Interference Explorer", report)
            if shutil.which("node"):
                scripts = re.findall(r"<script(?: [^>]*)?>([\s\S]*?)</script>", report)
                subprocess.run(
                    ["node", "-e", "new Function(process.argv[1])", scripts[-1]],
                    check=True,
                )


if __name__ == "__main__":
    unittest.main()
