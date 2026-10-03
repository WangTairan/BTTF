# Results

The archived direct-LLM predictions used in the paper are stored under
[`direct_llm/`](direct_llm/). All models and runs use the same compressed
JSONL schema. Each record contains the model and run, sample identity, human
and LLM readability scores, explanation, and token usage. The manifest records
observation counts and SHA-256 checksums.

Each file contains 3,900 observations: 1,100 human-rated programs and 2,800
controlled Java and Python variants. The three files for a model are its three
independent runs. Paper statistics first average the three scores for each
sample and then compute benchmark correlations or interference response rates.

Other generated evaluations and research analyses are ignored by Git because
they are reproduced by the released scripts. Their standard output layout is:

```text
methods/                        Primary-model and comparison-method predictions
experiments/readability_model/  Primary-model evaluations and analyses
```

Every report must identify its fixed feature configuration and evaluation
protocol. Historical result trees that do not support the paper are not part
of the release.

Publication figures derived from these results live in the tracked `figures/`
directory.
