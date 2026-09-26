"""Prompts for repository-level span completion."""

from __future__ import annotations


def span_completion_prompt(
    *, language: str, repository: str, source_path: str, source_with_hole: str
) -> str:
    tag = "java" if language == "java" else "python"
    return f"""Complete the single missing source-code span in this {language} file.

Return only the code that replaces <READABILITY_HOLE>. Do not return the full
file, Markdown fences, or an explanation. Preserve the surrounding behavior and
coding style.

Repository: {repository}
File: {source_path}

```{tag}
{source_with_hole}
```"""
