# LLOC baseline

This baseline counts language-aware statement and declaration nodes in the
source AST. Comments and blank physical lines are excluded:

```text
score = LLOC
```

The direction is intentionally simple: lower LLOC is predicted to be more
readable. For continuous readability datasets, the reported Spearman
correlation is therefore expected to be negative.
