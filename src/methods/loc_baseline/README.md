# LOC baseline

This baseline reports a snippet's non-empty line count directly:

```text
score = LOC
```

The direction is intentionally simple: lower LOC is predicted to be more
readable. For continuous readability datasets, the reported Spearman
correlation is therefore expected to be negative.
