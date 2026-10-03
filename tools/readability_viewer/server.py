"""Serve the local BTTF viewer without cloud APIs or a web framework."""
from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .diagnosis import Analyzer
from .catalog import Catalog
from .site import ResultSite, display_text
from .source_access import OFFICIAL_SOURCES, source_restricted, public_diagnosis

DIRECTORY = Path(__file__).resolve().parent


def make_handler(analyzer):
    inference_lock = threading.Lock()
    catalog = Catalog()
    site = ResultSite(catalog)

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type="application/json", filename=None):
            if not isinstance(body, bytes):
                body = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            try:
                if path in {"/", "/index.html"}:
                    return self.send(200, site.home().encode(), "text/html")
                if path == "/explainability.html":
                    return self.send(200, site.explainability_page().encode(), "text/html")
                if path.startswith("/assets/"):
                    filename = path.removeprefix("/assets/")
                    if filename in {"style.css", "app.js", "diagnosis.css", "diagnosis.js", "list.js", "theme.css", "theme.js", "favicon-light.svg", "favicon-dark.svg"}:
                        kind = ("image/svg+xml" if filename.endswith(".svg") else
                                "text/css" if filename.endswith(".css") else "text/javascript")
                        return self.send(200, (DIRECTORY.parents[1] / "docs/assets" / filename).read_bytes(), kind)
                parts = path.strip("/").split("/")
                if len(parts) == 2 and parts[0] == "explainability" and parts[1].endswith(".html"):
                    return self.send(200, site.explainability_page(parts[1][:-5]).encode(), "text/html")
                if len(parts) == 2 and parts[0] == "downloads" and parts[1].endswith(".json"):
                    dataset = parts[1][:-5]
                    if source_restricted(dataset):
                        self.send_response(302)
                        self.send_header("Location", OFFICIAL_SOURCES[dataset])
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    data = catalog.export_dataset(dataset)
                    return self.send(200, json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2).encode(),
                                     filename=f"{dataset}.json")
                if len(parts) == 2 and parts[0] == "methods" and parts[1].endswith(".html"):
                    return self.send(200, site.method_page(parts[1][:-5]).encode(), "text/html")
                if len(parts) == 2 and parts[0] == "datasets" and parts[1].endswith(".html"):
                    return self.send(200, site.dataset_page(parts[1][:-5]).encode(), "text/html")
                if len(parts) == 3 and parts[0] == "samples" and parts[2].endswith(".html"):
                    return self.send(200, site.sample_page(parts[1], int(parts[2][:-5])).encode(), "text/html")
            except (ValueError, KeyError, IndexError) as exc:
                return self.send(400, {"error": display_text(exc)})
            if path in {"/api/datasets", "/api/samples", "/api/diagnosis"}:
                try:
                    if path == "/api/datasets":
                        return self.send(200, catalog.datasets())
                    dataset = query.get("dataset", ["buse"])[0]
                    if path == "/api/samples":
                        return self.send(200, catalog.samples(dataset, query.get("q", [""])[0], int(query.get("page", ["0"])[0]), query.get("sort", ["source"])[0]))
                    index = int(query.get("index", ["0"])[0])
                    if not inference_lock.acquire(blocking=False):
                        return self.send(409, {"error": "An analysis is already running. Please wait."})
                    try:
                        result = catalog.diagnosis(dataset, index, analyzer)
                        return self.send(200, public_diagnosis(result, site.source_visible(dataset, index), dataset))
                    finally:
                        inference_lock.release()
                except Exception as exc:
                    return self.send(400, {"error": display_text(exc)})
            self.send(404, {"error": "Not found"})

        def do_POST(self):
            if self.path != "/api/analyze":
                return self.send(404, {"error": "Not found"})
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + self.headers.get("Host", ""):
                return self.send(403, {"error": "Use the viewer from its local browser page."})
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 250_000:
                return self.send(400, {"error": "Invalid request size"})
            if not inference_lock.acquire(blocking=False):
                return self.send(409, {"error": "An analysis is already running. Please wait."})
            try:
                request = json.loads(self.rfile.read(length))
                result = analyzer.analyze(request["source"], request.get("language", "java"), bool(request.get("fragments")))
                self.send(200, result)
            except Exception as exc:
                self.send(400, {"error": display_text(exc)})
            finally:
                inference_lock.release()

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--device", choices=("cpu", "mps", "cuda"), default="cpu")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(Analyzer(args.device)))
    print(f"BTTF viewer: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
