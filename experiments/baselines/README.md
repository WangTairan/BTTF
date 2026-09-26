# Comparison methods

This directory holds experiments that fit or evaluate published comparison
methods. Implementations remain under `src/methods/` and do not share the main
model's feature extractor. The retained `dorn/` runner reconstructs its
published feature model; other comparison methods expose their own runners.
