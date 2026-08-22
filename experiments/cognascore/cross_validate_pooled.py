"""Run pooled cross-validation for the frozen CognaScore feature set.

This descriptive entry point intentionally delegates to the original pooled
implementation so that previously reported results remain reproducible.
"""

from experiments.cognascore.cross_validate_fixed import main


if __name__ == "__main__":
    main()
