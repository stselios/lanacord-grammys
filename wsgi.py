"""
WSGI Application entry point for PythonAnywhere, Gunicorn, uWSGI, or any standard WSGI server.
"""

import os
import sys
import json
from urllib.parse import parse_qs

# Ensure this project folder is on Python's path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import server

STATUS_MAP = {
    200: "200 OK",
    201: "201 Created",
    204: "204 No Content",
    400: "400 Bad Request",
    401: "401 Unauthorized",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    500: "500 Internal Server Error"
}

def application(environ, start_response):
    """
    Standard WSGI application callable required by PythonAnywhere.
    """
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))

    headers = {}
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            header_name = k[5:].replace("_", "-").lower()
            headers[header_name] = v
        elif k in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            headers[k.replace("_", "-").lower()] = v

    body = {}
    if method == "POST":
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
            if content_length > 0:
                raw_body = environ["wsgi.input"].read(content_length).decode("utf-8")
                body = json.loads(raw_body)
        except Exception:
            err_body = json.dumps({"error": "Invalid JSON payload", "success": False}).encode("utf-8")
            start_response("400 Bad Request", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(err_body))),
                ("Access-Control-Allow-Origin", "*")
            ])
            return [err_body]

    status_code, resp_headers, resp_body = server.handle_request(method, path, query, headers, body)
    status_str = STATUS_MAP.get(status_code, f"{status_code} OK")

    response_headers_list = list(resp_headers.items())
    start_response(status_str, response_headers_list)
    return [resp_body]
