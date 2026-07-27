# Buse and Weimer readability dataset

Source: <https://web.eecs.umich.edu/~weimerw/data/readability/>

Local files:

- `raw/readability-snippets.zip`: original snippet archive.
- `raw/readability-votes.csv`: raw participant votes.
- `raw/readability-votes.html`: original HTML vote table copy.
- `snippets/*.jsnp`: extracted plain Java snippets used by the loader.
- `snippets/*.snip`: extracted HTML-highlighted versions, kept for provenance but
  not used by the loader.

The adapter loads 100 Java snippets. The readability score is the arithmetic
mean of all available Likert ratings for each snippet.
