from __future__ import annotations

import atexit
import base64
import os
import select
import subprocess
import threading
import time
from pathlib import Path

from src.methods.scalabrino.method import SCALABRINO_JAR


FEATURE_NAMES = (
    "Dorn-Visual-X-Identifiers",
    "Dorn-Visual-X-Comments",
    "Dorn-DFT-Comments",
    "Dorn-DFT-Numbers",
    "Dorn-DFT-Indentations",
    "Dorn-Areas-Operators",
    "Dorn-Visual-Y-Identifiers",
)
SUPPORTED_LANGUAGES = frozenset(("java", "python", "cuda"))
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve().parent / "java" / "DornFeatureServer.java"
BUILD_DIR = PROJECT_ROOT / "artifacts/baselines/dorn/java_adapter"
CLASS_PATH = BUILD_DIR / "DornFeatureServer.class"
RESULT_PREFIX = "DORN_RESULT\t"
REQUEST_TIMEOUT_SECONDS = 120.0


class DornExtractorError(RuntimeError):
    pass


class _DornFeatureProcess:
    def __init__(self, language: str) -> None:
        self.language = language
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None

    def extract(self, source: str) -> dict[str, float]:
        payload = base64.b64encode(source.encode("utf-8")).decode("ascii")
        with self._lock:
            for attempt in range(2):
                process = self._ensure_process()
                assert process.stdin is not None
                try:
                    process.stdin.write(payload + "\n")
                    process.stdin.flush()
                    return self._read_result(process)
                except (BrokenPipeError, EOFError, OSError, DornExtractorError):
                    self.close()
                    if attempt:
                        raise
            raise AssertionError("unreachable")

    def _ensure_process(self) -> subprocess.Popen[str]:
        if self._process is not None and self._process.poll() is None:
            return self._process
        compile_adapter()
        classpath = os.pathsep.join((str(BUILD_DIR.resolve()), str(SCALABRINO_JAR.resolve())))
        self._process = subprocess.Popen(
            ["java", "-cp", classpath, "DornFeatureServer", self.language],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        return self._process

    def _read_result(self, process: subprocess.Popen[str]) -> dict[str, float]:
        assert process.stdout is not None
        deadline = time.monotonic() + REQUEST_TIMEOUT_SECONDS
        diagnostics: list[str] = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                detail = " | ".join(diagnostics[-5:])
                raise DornExtractorError(
                    f"Dorn extraction timed out for {self.language}; output={detail!r}"
                )
            ready, _, _ = select.select([process.stdout], [], [], remaining)
            if not ready:
                continue
            line = process.stdout.readline()
            if not line:
                raise EOFError(
                    f"Dorn extractor exited with code {process.poll()}; "
                    f"output={' | '.join(diagnostics[-5:])!r}"
                )
            line = line.rstrip("\r\n")
            if not line.startswith(RESULT_PREFIX):
                diagnostics.append(line)
                continue
            fields = line.split("\t")
            if len(fields) >= 3 and fields[1] == "ERROR":
                message = base64.b64decode(fields[2]).decode("utf-8", errors="replace")
                raise DornExtractorError(message)
            if len(fields) != 2 + len(FEATURE_NAMES) or fields[1] != "OK":
                raise DornExtractorError(f"Malformed Dorn adapter response: {line!r}")
            return {
                name: float(value)
                for name, value in zip(FEATURE_NAMES, fields[2:])
            }

    def close(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


_compile_lock = threading.Lock()
_processes = {language: _DornFeatureProcess(language) for language in SUPPORTED_LANGUAGES}


def extract_dorn_features(code: str, language: str) -> dict[str, float]:
    normalized = language.strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported Dorn language: {language!r}")
    return _processes[normalized].extract(code)


def compile_adapter() -> None:
    if not SCALABRINO_JAR.is_file():
        raise FileNotFoundError(f"Scalabrino jar not found: {SCALABRINO_JAR}")
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Dorn Java adapter source not found: {SOURCE_PATH}")
    with _compile_lock:
        newest_input = max(SOURCE_PATH.stat().st_mtime, SCALABRINO_JAR.stat().st_mtime)
        if CLASS_PATH.is_file() and CLASS_PATH.stat().st_mtime >= newest_input:
            return
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(
            [
                "javac",
                "-cp",
                str(SCALABRINO_JAR.resolve()),
                "-d",
                str(BUILD_DIR.resolve()),
                str(SOURCE_PATH.resolve()),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if process.returncode != 0:
            raise DornExtractorError(
                f"Failed to compile Dorn Java adapter: {process.stdout.strip()}"
            )


def close_extractors() -> None:
    for process in _processes.values():
        process.close()


atexit.register(close_extractors)
