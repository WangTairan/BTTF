"""Integrity contract for the committed offline completion benchmark."""

from scripts.local_recent_completion_dataset import verify_archives


def test_pinned_completion_dataset_is_self_consistent():
    manifest = verify_archives()
    assert manifest["task_count"] == 507
    assert manifest["original_task_count"] == 48
    assert manifest["perturbed_task_count"] == 459
    assert manifest["target_count"] == 26
