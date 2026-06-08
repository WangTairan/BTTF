import subprocess
import tempfile
from dataclasses import dataclass
from math import isfinite, nan
from pathlib import Path


# Released Scalabrino assets are stored beside this implementation.
SCALABRINO_DIR = Path(__file__).resolve().parent / "official_tool"
SCALABRINO_JAR = SCALABRINO_DIR / "rsm.jar"


@dataclass
class ScalabrinoReadabilityResult:
    score: float
    level: str
    file_name: str
    raw_output: str


@dataclass
class ScalabrinoMetricsResult:
    metrics: dict[str, float]
    file_name: str
    raw_output: str


def scalabrino_model(code: str) -> ScalabrinoReadabilityResult:
    return scalabrino_source(code)


def scalabrino_source(code: str) -> ScalabrinoReadabilityResult:
    return scalabrino_java_source(prepare_java_source(code))


def scalabrino_java_source(code: str) -> ScalabrinoReadabilityResult:
    if not SCALABRINO_JAR.is_file():
        raise FileNotFoundError(f"Scalabrino jar not found: {SCALABRINO_JAR}")

    with tempfile.TemporaryDirectory(prefix="rmc_scalabrino_") as temp_dir:
        source_path = Path(temp_dir) / "Snippet.java"
        source_path.write_text(code, encoding="utf-8")
        return scalabrino_file(source_path)


def scalabrino_metrics(code: str) -> ScalabrinoMetricsResult:
    return scalabrino_java_source_metrics(prepare_java_source(code))


def scalabrino_java_source_metrics(code: str) -> ScalabrinoMetricsResult:
    if not SCALABRINO_JAR.is_file():
        raise FileNotFoundError(f"Scalabrino jar not found: {SCALABRINO_JAR}")

    with tempfile.TemporaryDirectory(prefix="rmc_scalabrino_") as temp_dir:
        source_path = Path(temp_dir) / "Snippet.java"
        source_path.write_text(code, encoding="utf-8")
        return scalabrino_file_metrics(source_path)


def prepare_java_source(code: str) -> str:
    if likely_complete_java_type(code):
        return code
    return (
        "import java.io.*;\n"
        "import java.lang.*;\n"
        "import java.util.*;\n"
        "import java.math.*;\n\n"
        "class Snippet {\n"
        f"{code}\n"
        "}\n"
    )


def likely_complete_java_type(code: str) -> bool:
    return any(
        marker in code
        for marker in (
            " class ",
            "class ",
            " interface ",
            "interface ",
            " enum ",
            "enum ",
            " record ",
            "record ",
        )
    )


def scalabrino_file(source_path: Path) -> ScalabrinoReadabilityResult:
    source_path = source_path.resolve()
    if not SCALABRINO_JAR.is_file():
        raise FileNotFoundError(f"Scalabrino jar not found: {SCALABRINO_JAR}")
    if not source_path.is_file():
        raise FileNotFoundError(f"Java source file not found: {source_path}")

    process = subprocess.run(
        ["java", "-jar", str(SCALABRINO_JAR), str(source_path)],
        cwd=str(SCALABRINO_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    raw_output = process.stdout.strip()
    if process.returncode != 0:
        raise RuntimeError(f"Scalabrino failed with exit code {process.returncode}: {raw_output}")

    return parse_scalabrino_output(raw_output)


def scalabrino_file_metrics(source_path: Path) -> ScalabrinoMetricsResult:
    source_path = source_path.resolve()
    if not SCALABRINO_JAR.is_file():
        raise FileNotFoundError(f"Scalabrino jar not found: {SCALABRINO_JAR}")
    if not source_path.is_file():
        raise FileNotFoundError(f"Java source file not found: {source_path}")

    process = subprocess.run(
        [
            "java",
            "-cp",
            str(SCALABRINO_JAR),
            "it.unimol.readability.metric.runnable.ExtractMetrics",
            str(source_path),
        ],
        cwd=str(SCALABRINO_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    raw_output = process.stdout.strip()
    if process.returncode != 0:
        raise RuntimeError(
            f"Scalabrino metric extraction failed with exit code {process.returncode}: "
            f"{raw_output}"
        )

    return ScalabrinoMetricsResult(
        metrics=parse_scalabrino_metrics_output(raw_output),
        file_name=str(source_path),
        raw_output=raw_output,
    )


def parse_scalabrino_output(raw_output: str) -> ScalabrinoReadabilityResult:
    for line in raw_output.splitlines():
        row = line.strip().split("\t")
        if len(row) < 2:
            continue
        try:
            score = float(row[-1])
        except ValueError:
            continue
        return ScalabrinoReadabilityResult(
            score=score,
            level=scalabrino_readability_level(score),
            file_name=row[0],
            raw_output=raw_output,
        )

    raise ValueError(f"Could not parse Scalabrino output: {raw_output!r}")


def parse_scalabrino_metrics_output(raw_output: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in raw_output.splitlines():
        name, separator, raw_value = line.partition(":")
        if not separator:
            continue
        name = name.strip()
        if not name:
            continue
        try:
            metrics[name] = float(raw_value.strip())
        except ValueError:
            if raw_value.strip().lower() == "nan":
                metrics[name] = nan
    if not metrics:
        raise ValueError(f"Could not parse Scalabrino metrics output: {raw_output!r}")
    return metrics


def scalabrino_readability_level(readability_score: float) -> str:
    if not isfinite(readability_score):
        return ""
    if readability_score <= 0.4:
        return "LOW"
    if readability_score <= 0.6:
        return "MEDIUM"
    return "HIGH"
