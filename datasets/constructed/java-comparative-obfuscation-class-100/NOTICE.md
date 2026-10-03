# Source attribution and modifications

This corpus contains 25 extracted production classes from each of four
projects, plus independently transformed variants. Original source paths and
line ranges are recorded in `manifest.jsonl`; `provenance.json` records the
construction procedure. The extracted classes are not complete project files:
file-level headers outside the extracted class were omitted. The notices here
preserve attribution for that extraction.

| Manifest source | Upstream project | Copyright / license |
| --- | --- | --- |
| `apache-kafka` | <https://github.com/apache/kafka> | The Apache Software Foundation; Apache-2.0 |
| `google-guava` | <https://github.com/google/guava> | Google and Guava contributors; Apache-2.0 |
| `netty` | <https://github.com/netty/netty> | The Netty Project and contributors; Apache-2.0 |
| `spring-framework` | <https://github.com/spring-projects/spring-framework> | Spring Framework authors; Apache-2.0 |

Full license: [`Apache-2.0.txt`](../../../licenses/third_party/Apache-2.0.txt).
Upstream notices: [`Kafka-NOTICE.txt`](../../../licenses/third_party/Kafka-NOTICE.txt)
and [`Netty-NOTICE.txt`](../../../licenses/third_party/Netty-NOTICE.txt).
Component references in these upstream notices do not mean their binaries are
included in this corpus.

Files under `source-original/` are extracted class text. Other source files
were modified by this study's named interference, as recorded per file in the
manifest. The transformation date is recorded in `provenance.json`. Upstream
licenses remain applicable to original excerpts and transformed variants;
this study does not relicense upstream code under its own code license.
