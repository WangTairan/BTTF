# Source attribution and modifications

This corpus contains 25 extracted production classes from each of four
projects, plus independently transformed variants. `manifest.jsonl` identifies
the original file and source lines; `provenance.json` pins all four source
repositories and commits. File-level headers outside an extracted class are
not present in the excerpt; their attribution and terms are retained here.

| Source | Upstream project | Copyright / license text |
| --- | --- | --- |
| Django | <https://github.com/django/django> | Django Software Foundation and individual contributors; [`BSD-3-Clause`](../../../licenses/third_party/Django-BSD-3-Clause.txt) |
| Flask | <https://github.com/pallets/flask> | Pallets; [`BSD-3-Clause`](../../../licenses/third_party/Flask-BSD-3-Clause.txt) |
| Requests | <https://github.com/psf/requests> | Kenneth Reitz and contributors; [`Apache-2.0`](../../../licenses/third_party/Apache-2.0.txt), [`NOTICE`](../../../licenses/third_party/Requests-NOTICE.txt) |
| attrs | <https://github.com/python-attrs/attrs> | Hynek Schlawack and attrs contributors; [`MIT`](../../../licenses/third_party/attrs-MIT.txt) |

Django also distributes code under the Python license; its original additional
notice is retained in [`Django-Python.txt`](../../../licenses/third_party/Django-Python.txt).

Files under `source-original/` are extracted class text. Other source files
were modified by this study's named interference, as recorded per file in the
manifest. The transformation date is recorded in `provenance.json`. Upstream
licenses remain applicable to original excerpts and transformed variants;
this study does not relicense upstream code under its own code license.
