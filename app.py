import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from query_rag import answer_question

PAGE = Path(__file__).with_name("static") / "index.html"
HOST = "127.0.0.1"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] not in ("/", "/index.html"):
            self.send_error(404)
            return
        body = PAGE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/ask":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "That question could not be read."})
            return
        question = str(payload.get("question", "")).strip()
        if not question:
            self._json(400, {"error": "Enter a question."})
            return
        if len(question) > 2000:
            self._json(400, {"error": "Keep the question under 2000 characters."})
            return
        try:
            answer = answer_question(question)
        except Exception as exc:
            self._json(500, {"error": f"The assistant could not answer: {exc}"})
            return
        self._json(200, {"answer": answer})

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Service Canada Assistant is at http://{HOST}:{PORT}")
    server.serve_forever()
