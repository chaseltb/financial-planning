"""
Launch script for the Financial Planning Platform.
Run from the project root: python run.py [optional_port]
"""
import os
import socket
import sys
from pathlib import Path

# Ensure the project root is on sys.path so 'planner' is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from planner.app import app


def find_free_port(start_port=8050):
    for p in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    return start_port


if __name__ == "__main__":
    requested_port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8050))
    # Test if requested port is free; if not, find the next available port
    target_port = find_free_port(requested_port)
    if target_port != requested_port:
        print(f"Notice: Port {requested_port} is busy or restricted. Using port {target_port} instead.")
    print(f"Starting Financial Planner on http://127.0.0.1:{target_port} ...")
    app.run(debug=False, host="127.0.0.1", port=target_port)


