# Mi ConvNetCR reproduction

This module independently reconstructs the character-level `ConvNetCR` branch
reported by Mi et al., *Improving Code Readability Classification Using
Convolutional Neural Networks* (IST 2018), DOI
`10.1016/j.infsof.2018.07.006`.

The reproduction covers the character-level branch. The authors' repository
provides the Java snippets and partial matrix-preprocessing utilities; the
network architecture and training settings follow the paper.

The implementation follows the paper's published character-level architecture:

- three line-spanning convolution banks with filter heights `(2, 2, 2)`;
- 100 feature maps per bank;
- ReLU, global max pooling, dropout `0.5`, and a two-way classifier;
- Adam with initial learning rate `0.001` and batch size `50`;
- readable/unreadable labels from the top and bottom quartiles of Buse, the Java
  subset of Dorn, and Scalabrino; the middle half is excluded.

The manifest records the architecture, training settings, and preprocessing.
The readable-class Softmax probability is used for Spearman and paired
interference evaluation.

Train and run Java interference evaluation with:

```bash
python -m src.methods.mi_convnet_cr.train

python -m src.experiments.evaluate_method \
  datasets/constructed/java-comparative-obfuscation-class-100 \
  --method mi_convnet_cr

python -m experiments.main.readability_model.evaluation.summarize_constructed_method \
  --dataset java_comparative_obfuscation --method mi_convnet_cr
```

Applying the Java-trained character model to Python is a cross-language transfer
diagnostic, not part of the protocol evaluated in the original paper.
