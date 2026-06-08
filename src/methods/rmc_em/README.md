# RMC_EM

Exact-mask Recursive Masking Complexity.

This variant uses the same mask generation as RMC control, but changes the
recovery contract. The model must return JSON with one replacement string per
`<mask>` token:

```json
{"masks": ["first mask content", "second mask content"]}
```

The score compares each returned mask replacement directly against the original
masked span, then averages the per-mask similarities. This avoids scoring the
entire reconstructed program when only the hidden regions matter.

