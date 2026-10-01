# LLM

Direct LLM readability scoring baseline. The model reads a code sample and
returns JSON with a readability score on a `0-20` scale plus a short reasoning
field.

Key parameter: the LLM model key. The paper baseline uses `dsv4-pro` through
the official DeepSeek API and requires `DEEPSEEK_API_KEY` in the environment.
Results are checkpointed per sample and preserve the raw response, token usage,
request parameters, and complete serializable API response for auditing.

```bash
python -m src.experiments.evaluate_method \
  datasets/mbjp_dev_dataset/readability_dataset.json \
  --method llm \
  --model dsv4-pro \
  --skip-existing \
  --require-llm-audit-record
```
