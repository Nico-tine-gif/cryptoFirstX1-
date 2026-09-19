"""Stdlib HTTP server for the admin control panel. No external deps."""
import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from core import config
from core.security.admin import AdminController
from core.admin.funds import AdminFunds
from core.p9.reconcile import reconcile
from core.security.gates import PolicyEngine
from core.security.audit import record
from .html import INDEX_HTML


def _login_from_env():
    name = os.environ.get("CRYPTOFIRSTX1_ADMIN")
    cred = os.environ.get("CRYPTOFIRSTX1_ADMIN_CREDENTIAL")
    if not name or not cred:
        sys.stderr.write(
            "ERROR: set CRYPTOFIRSTX1_ADMIN and "
            "CRYPTOFIRSTX1_ADMIN_CREDENTIAL before starting the panel\n"
        )
        raise SystemExit(2)
    os.environ["CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256"] = (
        hashlib.sha256(cred.encode()).hexdigest()
    )
    admin = AdminController()
    admin.authenticate(name, cred)
    if not admin.authorized():
        sys.stderr.write("ERROR: authentication failed\n")
        raise SystemExit(3)
    return admin


class Handler(BaseHTTPRequestHandler):
    admin = None
    engine = None

    def log_message(self, fmt, *args):
        # Quieter logs — one line per request
        sys.stderr.write("[panel] %s\n" % (fmt % args))

    # --------------------------------------------------------------
    # helpres
    # --------------------------------------------------------------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _funds(self):
        return AdminFunds(self.admin)

    # --------------------------------------------------------------
    # GET
    # --------------------------------------------------------------
    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        p = u.path

        try:
            if p == "/" or p == "/index.html":
                return self._send_html(INDEX_HTML)

            if p == "/api/dashboard":
                return self._send_json(self._funds().dashboard())

            if p == "/api/security":
                return self._send_json(self._funds().security_status())

            if p == "/api/deposits":
                return self._send_json({
                    "entries": self._funds().deposits(
                        limit=int(q.get("limit", ["100"])[0]))})

            if p == "/api/withdrawals":
                return self._send_json({
                    "entries": self._funds().withdrawals(
                        limit=int(q.get("limit", ["100"])[0]))})

            if p == "/api/ledger":
                return self._send_json({
                    "entries": self._funds().ledger_history(
                        limit=int(q.get("limit", ["100"])[0]))})

            if p == "/api/reconcile":
                r = reconcile()
                return self._send_json({
                    "chain_deposits": r.chain_count,
                    "ledger_credits": r.credited_count,
                    "matched":        r.both_sides_count,
                    "pending_credit": r.pending_credit,
                    "orphan_credits": r.orphan_credits,
                    "non_admin_accounts": r.non_admin_accounts,
                    "balanced":       r.balanced,
                })

            if p == "/api/policy":
                return self._send_json(self.engine.snapshot())

            if p == "/api/allowlist":
                entries = [list(e) for e in self.engine.allowlist.entries()]
                return self._send_json({"entries": entries})

            return self._send_json({"error": "not found"}, 404)

        except Exception as e:
            return self._send_json(
                {"error": f"{type(e).__name__}: {e}"}, 500)

    # --------------------------------------------------------------
    # POST
    # --------------------------------------------------------------
    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        p = u.path

        try:
            if p == "/api/lock":
                self.admin.lock()
                record("PANEL_LOCK", actor="panel")
                return self._send_json({"ok": True, "locked": True})

            if p == "/api/unlock":
                self.admin.unlock()
                record("PANEL_UNLOCK", actor="panel")
                return self._send_json({"ok": True, "locked": False})

            if p == "/api/allowlist/add":
                addr = (q.get("address") or [""])[0]
                if not addr:
                    return self._send_json({"error": "address required"}, 400)
                self.engine.allowlist.add(addr)
                record("PANEL_ALLOWLIST_ADD", actor="panel",
                       address=addr)
                return self._send_json({"ok": True, "address": addr})

            if p == "/api/allowlist/remove":
                addr = (q.get("address") or [""])[0]
                self.engine.allowlist.remove(addr)
                record("PANEL_ALLOWLIST_REMOVE", actor="panel",
                       address=addr)
                return self._send_json({"ok": True, "address": addr})

            return self._send_json({"error": "not found"}, 404)

        except Exception as e:
            return self._send_json(
                {"error": f"{type(e).__name__}: {e}"}, 500)


def serve(host=None, port=None):
    host = host or config.PANEL_HOST
    port = port or config.PANEL_PORT

    admin = _login_from_env()
    Handler.admin = admin
    Handler.engine = PolicyEngine(admin)

    server = HTTPServer((host, port), Handler)
    print(f"admin panel listening on http://{host}:{port}")
    print("press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.server_close()
