# LLM

Direct LLM readability scoring baseline. The model reads a code sample and
returns JSON with a readability score on a `0-20` scale plus a short reasoning
field.

Key parameter: the LLM model, for example `gpt41-nano`.

```bash
python3 -m src.experiments.evaluate_method \
  datasets/mbjp_dev_dataset/readability_dataset.json \
  --method llm \
  --model gpt41-nano
```

