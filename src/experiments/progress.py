import sys


class ProgressBar:
    def __init__(self, label: str, total: int, width: int = 24) -> None:
        self.label = label
        self.total = max(int(total), 0)
        self.width = width
        self.active = False

    def update(self, status: str, completed: int, total: int | None = None) -> None:
        total = max(int(total if total is not None else self.total), 1)
        completed = min(max(int(completed), 0), total)
        filled = int(self.width * completed / total)
        bar = "#" * filled + "-" * (self.width - filled)
        text = f"{self.label} [{bar}] {completed}/{total} | {status}"
        if sys.stdout.isatty():
            print(f"\r{text}", end="", flush=True)
        else:
            print(text, flush=True)
        self.active = True

    def finish(self) -> None:
        if self.active and sys.stdout.isatty():
            print(flush=True)
        self.active = False

    def callback(self):
        return self.update


class DatasetProgress:
    def __init__(self, total: int, *, unit_label: str = "samples") -> None:
        self.total = max(int(total), 0)
        self.unit_label = unit_label

    def message(self, index: int, status: str, task_id: str) -> None:
        print(f"[{index}/{self.total}] {status} {task_id}", flush=True)

    def running(self, index: int, task_id: str) -> None:
        self.message(index, "Running", task_id)

    def skipping(self, index: int, task_id: str) -> None:
        self.message(index, "Skipping", task_id)

    def writing(self, index: int, task_id: str) -> None:
        self.message(index, "Writing", task_id)

    def wrote(self, index: int, task_id: str) -> None:
        self.message(index, "Wrote", task_id)

    def bar(self, index: int, task_id: str, *, label: str = "masks") -> ProgressBar:
        prefix = f"{self.unit_label} {index}/{self.total} | {label}"
        return ProgressBar(f"{prefix} | {task_id}", total=0)


def batch_progress(label: str = "batch"):
    bar = ProgressBar(label, total=0)

    def update(status: str, completed: int, total: int) -> None:
        bar.update(status, completed, total)

    return update
