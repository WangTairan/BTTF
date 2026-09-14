from __future__ import annotations


def build_candidate(
    common: dict[str, object],
    mutation_anchors: list[dict[str, object]],
) -> dict[str, object] | None:
    if not mutation_anchors:
        return None
    base_sample_id = str(common["base_sample_id"])
    return {
        **common,
        "experiment": "test-guided-repair",
        "candidate_id": f"repair-{base_sample_id}",
        "mutation_anchors": mutation_anchors,
        "mutation_anchor_count": len(mutation_anchors),
        "injection_order": "readability_interference_then_aligned_bug_injection",
        "required_validation": [
            "restore_upstream_context",
            "build_project",
            "run_clean_tests",
            "inject_aligned_mutation",
            "run_mutant_tests",
            "verify_test_kill",
        ],
    }
