"""Pinned targets for the recent-repository completion pilot.

The pilot names concrete, recently changed production symbols. It does not
sample arbitrary old methods merely because their repository remains active.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryTarget:
    repository_id: str
    repository_url: str
    license_spdx: str
    language: str
    pinned_commit: str
    target_origin_commit: str
    target_origin_date: str
    source_path: str
    symbol: str
    signature_contains: str | None
    test_args: tuple[str, ...]


@dataclass(frozen=True)
class RepositorySpec:
    repository_id: str
    repository_url: str
    directory: str
    license_spdx: str
    language: str
    pinned_commit: str
    since_date: str
    source_roots: tuple[str, ...]
    test_roots: tuple[str, ...]


REPOSITORIES = (
    RepositorySpec(
        repository_id="apache-commons-collections",
        repository_url="https://github.com/apache/commons-collections.git",
        directory="commons-collections",
        license_spdx="Apache-2.0",
        language="java",
        pinned_commit="21d6821190e0325022510393f41faa8ec95b6397",
        since_date="2026-01-01",
        source_roots=("src/main/java",),
        test_roots=("src/test/java",),
    ),
    RepositorySpec(
        repository_id="pytest",
        repository_url="https://github.com/pytest-dev/pytest.git",
        directory="pytest",
        license_spdx="MIT",
        language="python",
        pinned_commit="53bc06b9933eb50b40cd904aa50bcd1b6cf2a49c",
        since_date="2026-01-01",
        source_roots=("src/_pytest",),
        test_roots=("testing",),
    ),
)


PILOT_TARGETS = (
    RepositoryTarget(
        repository_id="apache-commons-collections",
        repository_url="https://github.com/apache/commons-collections.git",
        license_spdx="Apache-2.0",
        language="java",
        pinned_commit="21d6821190e0325022510393f41faa8ec95b6397",
        target_origin_commit="b0ce37f0d62f0a6efa306d90d446f6d0f9549bdb",
        target_origin_date="2026-09-03",
        source_path=(
            "src/main/java/org/apache/commons/collections4/multimap/"
            "TransformedMultiValuedMap.java"
        ),
        symbol="putAll",
        signature_contains="Iterable<? extends V> values",
        test_args=(
            "mvn",
            "-q",
            "-Dmaven.repo.local={maven_repo}",
            "-Drat.skip=true",
            "-DskipTests=false",
            "-Dtest=TransformedMultiValuedMapTest",
            "test",
        ),
    ),
    RepositoryTarget(
        repository_id="pytest",
        repository_url="https://github.com/pytest-dev/pytest.git",
        license_spdx="MIT",
        language="python",
        pinned_commit="53bc06b9933eb50b40cd904aa50bcd1b6cf2a49c",
        target_origin_commit="b7c1834d814749a6ee8e3a002deba53068313ec4",
        target_origin_date="2026-09-13",
        source_path="src/_pytest/approx.py",
        symbol="_contains_decimal",
        signature_contains=None,
        test_args=(
            "{python}",
            "-m",
            "pytest",
            "-q",
            "testing/python/approx.py",
            "-k",
            "inexact_float_tolerance",
        ),
    ),
)
