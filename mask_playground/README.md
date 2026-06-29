# Mask Recovery Lab

Local interactive interface for selecting one source region, masking it, sending
the configured RMC prompt to a selected model, and inspecting the extracted mask
replacement.

The left editor loads selectable MBJP, Scalabrino, JetBrains, Dorn, and
Schnappinger samples. Language is bound to each sample and Java, Python, or CUDA
highlighting is applied automatically. Human readability labels are intentionally
not exposed in this experimental interface. Each of the three immutable prompt
variants has a separate custom cache slot. The prompt panel separates the system
instructions, few-shot examples, and current mask task, with an additional
combined view. Editing the first two sections switches to the template's custom
slot; the current mask is always generated from the source editor and is never
cached.
The completed-code view replaces only the selected mask region and preserves all
source text before and after it. Each response reports exact match, sequence,
token Jaccard, token cosine, and BLEU similarities. Edit distance and other
quadratic dynamic-programming metrics are intentionally excluded.

The browser never receives API keys. Model calls run through `src.services.llm`
in the Python server process.

```bash
cd <REPOSITORY_ROOT>
python3 -m mask_playground.server
```

Open `http://127.0.0.1:8765`.
