# Dorn six-dataset evaluation

This experiment holds the seven-feature Dorn representation fixed and fits the
same dataset-balanced Ridge protocol used for CognaScore. It reports pooled
10-fold validation, leave-one-dataset-out validation, and a descriptive fit on
the complete six-dataset training pool.

Feature extraction uses the compiled Dorn metric implementation in the released
Scalabrino tool. Per-item feature caches are content-addressed and resumable.
