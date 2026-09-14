from __future__ import annotations


def build_candidate(common: dict[str, object]) -> dict[str, object]:
    base_sample_id = str(common["base_sample_id"])
    return {
        **common,
        "experiment": "behavior-prediction",
        "candidate_id": f"behavior-{base_sample_id}",
        "required_validation": [
            "restore_upstream_context",
            "build_project",
            "derive_fixed_input",
            "execute_original",
            "execute_changed_variants",
            "verify_equal_oracle",
        ],
    }
