# Scalabrino

This package provides the Scalabrino readability model from Scalabrino et al.,
*A Comprehensive Model for Code Readability* (JSEP 2018).

The official download contains compiled assets only:

- `rsm.jar`
- `readability.classifier`
- `README.md`

No source code is included in the official archive. The assets in
`official_tool/` are copied from the official `readability.zip` downloaded from
`https://dibt.unimol.it/report/readability/files/readability.zip`.

Official archive checksum:

```text
readability.zip  e556b9b05ed14ed76c122170bd7d43fbc39cf80b8acac2930caebe96ac284329
```

Stored asset checksums:

```text
rsm.jar                 2df38f4fecaf84806f5600329ff7eea53fad11ed47892c973e6932c189790b92
readability.classifier  5a3ec858d5abc0b28a62070a892f52b58eaacf530ff091b01e579de1c2beab4d
README.md               1c329c1764b04ca7ec8e369f9dd82340c93fdc11c37c446aaa88ae5cf70c3561
```

## Interface

The public experiment method is `scalabrino`; the Python entry point is
`scalabrino_model(code)`. It calls the released jar
directly. Because the released tool expects Java source files and some of our
datasets contain method snippets, snippets are placed in a minimal enclosing
class before scoring.

The package also exposes metric extraction through the official jar entry point:

```bash
java -cp rsm.jar it.unimol.readability.metric.runnable.ExtractMetrics <file.java>
```

Use `scalabrino_metrics(code)` from Python to obtain the extracted
structural, visual, and textual feature values as a dictionary.
