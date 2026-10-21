import os
import socket
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)


def get_free_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + max_attempts - 1}")


if __name__ == "__main__":
    preferred_port = int(os.environ.get("PORT", "8000"))
    port = get_free_port(preferred_port)
    if port != preferred_port:
        print(f"Port {preferred_port} was busy; using port {port} instead.")

    print(f"Starting application on http://127.0.0.1:{port}")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
