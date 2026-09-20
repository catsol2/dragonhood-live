from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os

# Render.com dynamic port support karta hai[cite: 6]
PORT = int(os.environ.get("PORT", 5500))

ROOT = os.path.dirname(os.path.abspath(__file__))[cite: 6]

X_CLIENT_ID = "clFGTHhES1UzWkhsbzNOb1pKMzk6MTpjaQ"[cite: 6]

X_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"[cite: 6]
X_ME_URL = "https://api.twitter.com/2/users/me"[cite: 6]


class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)[cite: 6]

    def send_json(self, status, data):
        raw = json.dumps(data).encode("utf-8")[cite: 6]
        self.send_response(status)[cite: 6]
        self.send_header("Content-Type", "application/json; charset=utf-8")[cite: 6]
        self.send_header("Content-Length", str(len(raw)))[cite: 6]
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")[cite: 6]
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")[cite: 6]
        self.end_headers()[cite: 6]
        self.wfile.write(raw)[cite: 6]

    def do_OPTIONS(self):
        self.send_response(204)[cite: 6]
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")[cite: 6]
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")[cite: 6]
        self.end_headers()[cite: 6]

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))[cite: 6]
        body = self.rfile.read(length)[cite: 6]
        if not body:
            return {}[cite: 6]
        try:
            return json.loads(body.decode("utf-8"))[cite: 6]
        except Exception:
            return None[cite: 6]

    def do_POST(self):
        path = urlparse(self.path).path[cite: 6]
        data = self.read_json()[cite: 6]

        if data is None:
            self.send_json(400, {"error": "invalid_json"})[cite: 6]
            return[cite: 6]

        # --------------------------------------------------
        # X TOKEN EXCHANGE
        # --------------------------------------------------
        if path == "/api/x-token":[cite: 6]
            code = data.get("code")[cite: 6]
            code_verifier = data.get("code_verifier")[cite: 6]
            redirect_uri = data.get("redirect_uri")[cite: 6]

            if not code or not code_verifier or not redirect_uri:
                self.send_json(400, {"error": "missing_required_parameters"})
                return

            form = urlencode({[cite: 6]
                "code": code,[cite: 6]
                "grant_type": "authorization_code",[cite: 6]
                "client_id": X_CLIENT_ID,[cite: 6]
                "redirect_uri": redirect_uri,[cite: 6]
                "code_verifier": code_verifier[cite: 6]
            })

            request = Request([cite: 6]
                X_TOKEN_URL,[cite: 6]
                data=form.encode("utf-8"),[cite: 6]
                headers={"Content-Type": "application/x-www-form-urlencoded"},[cite: 6]
                method="POST"[cite: 6]
            )

            try:
                with urlopen(request, timeout=30) as response:[cite: 6]
                    raw = response.read()[cite: 6]
                    try:
                        result = json.loads(raw.decode("utf-8"))[cite: 6]
                    except Exception:
                        result = {"error": "invalid_x_response", "raw": raw.decode("utf-8", errors="replace")}[cite: 6]
                    self.send_json(response.status, result)[cite: 6]
                return[cite: 6]

            except HTTPError as error:[cite: 6]
                raw = error.read()[cite: 6]
                try:
                    result = json.loads(raw.decode("utf-8"))[cite: 6]
                except Exception:
                    result = {"error": "x_token_http_error", "status": error.code, "raw": raw.decode("utf-8", errors="replace")}[cite: 6]
                self.send_json(error.code, result)[cite: 6]
                return[cite: 6]

            except URLError as error:[cite: 6]
                self.send_json(502, {"error": "x_token_network_error", "details": str(error)})[cite: 6]
                return[cite: 6]

            except Exception as error:[cite: 6]
                self.send_json(500, {"error": "x_token_server_error", "details": str(error)})[cite: 6]
                return[cite: 6]

        # --------------------------------------------------
        # X USER INFO
        # --------------------------------------------------
        if path == "/api/x-me":[cite: 6]
            access_token = data.get("access_token")[cite: 6]
            if not access_token:[cite: 6]
                self.send_json(400, {"error": "missing_access_token"})[cite: 6]
                return[cite: 6]

            request = Request([cite: 6]
                X_ME_URL,[cite: 6]
                headers={"Authorization": "Bearer " + access_token},[cite: 6]
                method="GET"[cite: 6]
            )

            try:
                with urlopen(request, timeout=30) as response:[cite: 6]
                    raw = response.read()[cite: 6]
                    try:
                        result = json.loads(raw.decode("utf-8"))[cite: 6]
                    except Exception:
                        result = {"error": "invalid_x_me_response", "raw": raw.decode("utf-8", errors="replace")}[cite: 6]
                    self.send_json(response.status, result)[cite: 6]
                return[cite: 6]

            except HTTPError as error:[cite: 6]
                raw = error.read()[cite: 6]
                try:
                    result = json.loads(raw.decode("utf-8"))[cite: 6]
                except Exception:
                    result = {"error": "x_me_http_error", "status": error.code, "raw": raw.decode("utf-8", errors="replace")}[cite: 6]
                self.send_json(error.code, result)[cite: 6]
                return[cite: 6]

            except URLError as error:[cite: 6]
                self.send_json(502, {"error": "x_me_network_error", "details": str(error)})[cite: 6]
                return[cite: 6]

            except Exception as error:[cite: 6]
                self.send_json(500, {"error": "x_me_server_error", "details": str(error)})[cite: 6]
                return[cite: 6]

        if path.startswith("/api/"):[cite: 6]
            self.send_json(404, {"error": "api_route_not_found", "path": path})[cite: 6]
            return[cite: 6]

        self.send_error(404)[cite: 6]


if __name__ == "__main__":
    print("")[cite: 6]
    print("========================================")[cite: 6]
    print(" DRAGONHOOD X OAUTH SERVER")[cite: 6]
    print("========================================")[cite: 6]
    print("Folder :", ROOT)[cite: 6]
    print("Port   :", PORT)
    print("Domain : https://dragonhood.xyz")
    print("Press CTRL+C to stop.")[cite: 6]
    print("")[cite: 6]

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()[cite: 6]