# LLM

Direct LLM readability scoring baseline. The model reads a code sample and
returns JSON with a readability score on a `0-20` scale plus a short reasoning
field.

Key parameter: the LLM model key. The main paper evaluates `dsv4-pro` and
`gpt61-sol`; the supplement also reports `gpt6-sol`. Each sample is scored in
three independent runs, and the three scores are averaged for analysis.
Results are checkpointed per sample and preserve the raw response, token usage,
and request metadata. Provider runs require the corresponding credential.
The paper inputs are archived in a common model/run schema under
[`results/direct_llm/`](../../../results/direct_llm/).

```bash
python -m src.experiments.evaluate_method \
  datasets/mbjp_dev_dataset/readability_dataset.json \
  --method llm \
  --model dsv4-pro \
  --skip-existing \
  --require-llm-audit-record
```
