from __future__ import annotations

from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    apply_edits,
    tree,
    walk,
)


class RemoveComments(Interference):
    category = "comments"
    slug = "remove-comments"
    description = "Remove line comments, block comments, and Javadoc"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        comments = [
            node
            for node in walk(tree(source).root_node)
            if node.type in {"block_comment", "line_comment"}
        ]
        edits = []
        removed_bytes = 0
        for node in comments:
            original = source[node.start_byte : node.end_byte]
            replacement = b"\n" * original.count(b"\n") or b" "
            edits.append((node.start_byte, node.end_byte, replacement))
            removed_bytes += len(original) - len(replacement)
        return TransformResult(
            apply_edits(source, edits),
            {
                "comments_removed": len(comments),
                "comment_bytes_removed": removed_bytes,
            },
        )
