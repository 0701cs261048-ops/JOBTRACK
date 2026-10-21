"""JobTrack backend: REST API + SQLite + token auth. Python standard library only."""
import json, os, re, secrets, sqlite3, hashlib, hmac, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get("DB_PATH", "tracker.db")
HERE = os.path.dirname(os.path.abspath(__file__))
STATUSES = ("Applied", "Interview", "Offer", "Rejected")
SESSION_TTL = 30 * 86400


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL, pw_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL
            REFERENCES users(id) ON DELETE CASCADE, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS apps(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL
            REFERENCES users(id) ON DELETE CASCADE, company TEXT NOT NULL, role TEXT NOT NULL,
            status TEXT NOT NULL, date TEXT NOT NULL, link TEXT DEFAULT '', notes TEXT DEFAULT '');
        CREATE INDEX IF NOT EXISTS idx_apps_user ON apps(user_id);
        """)


def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000).hex()


class Err(Exception):
    def __init__(self, code, msg):
        self.code, self.msg = code, msg


def clean_app(d):
    out = {k: str(d.get(k, "")).strip() for k in ("company", "role", "status", "date", "link", "notes")}
    if not out["company"] or not out["role"] or len(out["company"]) > 80 or len(out["role"]) > 80:
        raise Err(400, "Company and role are required (max 80 characters).")
    if out["status"] not in STATUSES:
        raise Err(400, "Invalid status.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", out["date"]):
        raise Err(400, "Date must be YYYY-MM-DD.")
    if out["link"] and not re.match(r"https?://", out["link"], re.I):
        raise Err(400, "Link must start with http:// or https://.")
    if len(out["notes"]) > 500 or len(out["link"]) > 300:
        raise Err(400, "Notes or link too long.")
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 20000:
            raise Err(413, "Request too large.")
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            raise Err(400, "Invalid JSON.")

    def user(self, c):
        tok = (self.headers.get("Authorization") or "").replace("Bearer ", "", 1)
        r = c.execute("SELECT user_id, created FROM sessions WHERE token=?", (tok,)).fetchone()
        if not r or time.time() - r["created"] > SESSION_TTL:
            raise Err(401, "Please log in.")
        return r["user_id"], tok

    def handle_any(self, method):
        try:
            path = self.path.split("?")[0]
            if method == "GET" and path == "/":
                with open(os.path.join(HERE, "index.html"), "rb") as f:
                    return self.send(200, f.read(), "text/html; charset=utf-8")
            if not path.startswith("/api/"):
                raise Err(404, "Not found.")
            with db() as c:
                self.route(c, method, path[5:])
        except Err as e:
            self.send(e.code, {"error": e.msg})
        except Exception:
            self.send(500, {"error": "Server error."})

    def route(self, c, method, p):
        if method == "POST" and p in ("register", "login"):
            d = self.body()
            email, pw = str(d.get("email", "")).strip().lower(), str(d.get("password", ""))
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 120:
                raise Err(400, "Enter a valid email.")
            if p == "register":
                if len(pw) < 8:
                    raise Err(400, "Password must be at least 8 characters.")
                salt = secrets.token_bytes(16)
                try:
                    uid = c.execute("INSERT INTO users(email,salt,pw_hash) VALUES(?,?,?)",
                                    (email, salt, hash_pw(pw, salt))).lastrowid
                except sqlite3.IntegrityError:
                    raise Err(409, "That email is already registered.")
            else:
                u = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                if not u or not hmac.compare_digest(u["pw_hash"], hash_pw(pw, u["salt"])):
                    raise Err(401, "Wrong email or password.")
                uid = u["id"]
            tok = secrets.token_urlsafe(32)
            c.execute("INSERT INTO sessions VALUES(?,?,?)", (tok, uid, time.time()))
            return self.send(200, {"token": tok, "email": email})

        uid, tok = self.user(c)
        if method == "POST" and p == "logout":
            c.execute("DELETE FROM sessions WHERE token=?", (tok,))
            return self.send(200, {"ok": True})
        if method == "GET" and p == "me":
            return self.send(200, {"email": c.execute("SELECT email FROM users WHERE id=?", (uid,)).fetchone()[0]})
        if p == "apps" and method == "GET":
            rows = c.execute("SELECT * FROM apps WHERE user_id=? ORDER BY date DESC, id DESC", (uid,))
            return self.send(200, [dict(r) for r in rows])
        if p == "apps" and method == "POST":
            a = clean_app(self.body())
            a["id"] = c.execute("INSERT INTO apps(user_id,company,role,status,date,link,notes) VALUES(?,?,?,?,?,?,?)",
                                (uid, a["company"], a["role"], a["status"], a["date"], a["link"], a["notes"])).lastrowid
            return self.send(201, a)
        m = re.fullmatch(r"apps/(\d+)", p)
        if m and method in ("PUT", "DELETE"):
            aid = int(m.group(1))
            if method == "DELETE":
                n = c.execute("DELETE FROM apps WHERE id=? AND user_id=?", (aid, uid)).rowcount
            else:
                a = clean_app(self.body())
                n = c.execute("UPDATE apps SET company=?,role=?,status=?,date=?,link=?,notes=? WHERE id=? AND user_id=?",
                              (a["company"], a["role"], a["status"], a["date"], a["link"], a["notes"], aid, uid)).rowcount
            if not n:
                raise Err(404, "Application not found.")
            return self.send(200, {"ok": True})
        if p == "stats" and method == "GET":
            counts = {s: 0 for s in STATUSES}
            for r in c.execute("SELECT status, COUNT(*) n FROM apps WHERE user_id=? GROUP BY status", (uid,)):
                counts[r["status"]] = r["n"]
            total = sum(counts.values())
            heard = total - counts["Applied"]
            days = [time.strftime("%Y-%m-%d", time.localtime(time.time() - i * 86400)) for i in range(6, -1, -1)]
            per = {r["date"]: r["n"] for r in c.execute(
                "SELECT date, COUNT(*) n FROM apps WHERE user_id=? AND date>=? GROUP BY date", (uid, days[0]))}
            return self.send(200, {"counts": counts, "total": total,
                                   "heard_back_pct": round(100 * heard / total) if total else 0,
                                   "last7": [{"date": d, "n": per.get(d, 0)} for d in days]})
        raise Err(404, "Not found.")

    def do_GET(self): self.handle_any("GET")
    def do_POST(self): self.handle_any("POST")
    def do_PUT(self): self.handle_any("PUT")
    def do_DELETE(self): self.handle_any("DELETE")


if __name__ == "__main__":
    init()
    port = int(os.environ.get("PORT", 10000))
print(f"JobTrack running on port {port}")
ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
