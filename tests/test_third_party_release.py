import csv
import hashlib
import json
import re
from pathlib import Path, PureWindowsPath

from src.datasets.schnappinger import load_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_curated_schnappinger_preserves_evaluated_sources_and_labels():
    root = ROOT / "datasets/schnappinger"
    inventory = json.loads((root / "source_inventory.json").read_text())
    assert inventory["sample_count"] == 304
    assert hashlib.sha256((root / "labels.csv").read_bytes()).hexdigest() == inventory["label_sha256"]
    with (root / "labels.csv").open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    labelled = {"/".join(PureWindowsPath(row["path"]).parts).casefold() for row in rows}
    assert {row["path"].casefold() for row in inventory["sources"]} == labelled
    for row in inventory["sources"]:
        assert hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    assert len(load_dataset(root)) == 304
    files = [path for path in root.rglob("*") if path.is_file()]
    assert not any(path.suffix.lower() in {".jar", ".class", ".pdf"} for path in files)
    assert {path.relative_to(root).as_posix() for path in files if path.suffix == ".java"} == {
        row["path"] for row in inventory["sources"]
    }


def test_schnappinger_jsweet_alias_on_case_sensitive_layout(tmp_path):
    root = ROOT / "datasets/schnappinger"
    with (root / "labels.csv").open(encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        row = next(row for row in reader if row["path"].startswith("jsweet"))
    with (tmp_path / "labels.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
    parts = PureWindowsPath(row["path"]).parts
    source = tmp_path.joinpath("Jsweet", *parts[1:])
    source.parent.mkdir(parents=True)
    source.write_text("public class PreservedSource {}\n")
    assert load_dataset(tmp_path)[0].content == "public class PreservedSource {}\n"


def test_third_party_notice_links_resolve():
    notices = [
        ROOT / "THIRD_PARTY.md",
        ROOT / "licenses/third_party/README.md",
        ROOT / "datasets/mbjp_dev_dataset/NOTICE.md",
        ROOT / "datasets/jetbrains/README.md",
        ROOT / "datasets/schnappinger/NOTICE.md",
        ROOT / "datasets/constructed/java-comparative-obfuscation-class-100/NOTICE.md",
        ROOT / "datasets/constructed/python-comparative-degradation-class-100/NOTICE.md",
        ROOT / "src/methods/readability_model/resources/semantic_anchor_corpus/NOTICE.md",
    ]
    for notice in notices:
        for link in re.findall(r"\]\(([^)]+)\)", notice.read_text()):
            if not link.startswith(("https://", "http://", "#")):
                assert (notice.parent / link).exists(), (notice, link)
