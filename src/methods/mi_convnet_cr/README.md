# Mi ConvNetCR reproduction

This module independently reconstructs the character-level `ConvNetCR` branch
reported by Mi et al., *Improving Code Readability Classification Using
Convolutional Neural Networks* (IST 2018), DOI
`10.1016/j.infsof.2018.07.006`.

It is deliberately named `mi_convnet_cr`, not `DeepCRM`. The authors' public
repository provides Java snippets and partial matrix-preprocessing utilities,
but does not provide the CNN implementation, trained weights, character
dictionary, or all dependencies needed to reconstruct the complete three-view
ensemble. Calling an independently completed ensemble the official DeepCRM
would therefore overstate reproducibility.

The implementation follows the paper's published character-level architecture:

- three line-spanning convolution banks with filter heights `(2, 2, 2)`;
- 100 feature maps per bank;
- ReLU, global max pooling, dropout `0.5`, and a two-way classifier;
- Adam with initial learning rate `0.001` and batch size `50`;
- readable/unreadable labels from the top and bottom quartiles of Buse, the Java
  subset of Dorn, and Scalabrino; the middle half is excluded.

The frozen-model manifest separates paper-specified settings from choices that
the incomplete release forces a reproduction to make. The readable-class
Softmax probability is exposed as the continuous score for Spearman and paired
degradation evaluation.

Train and run the external Java interference evaluation with:

```bash
PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 -m src.methods.mi_convnet_cr.train

PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 -m src.experiments.evaluate_method \
  datasets/constructed/java-comparative-obfuscation-class-100 \
  --method mi_convnet_cr

PYTHONPYCACHEPREFIX=/tmp/readability_pycache \
python3 -m experiments.cognascore.summarize_constructed_method \
  --dataset java_comparative_obfuscation --method mi_convnet_cr
```

Applying the Java-trained character model to Python is a cross-language transfer
diagnostic, not part of the protocol evaluated in the original paper.
