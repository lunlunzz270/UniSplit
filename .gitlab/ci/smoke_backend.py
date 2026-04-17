import json
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
BASE_URL = "http://127.0.0.1:5000"


def wait_for_server(timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/", timeout=2).read()
            return
        except Exception:
            time.sleep(1)
    raise SystemExit("backend did not start in time")


def main() -> int:
    # Capture logs to a file so we can read them if it fails
    log_file = open("backend_smoke.log", "w")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "flask",
            "--app",
            "main",
            "run",
            "--host=127.0.0.1",
            "--port=5000",
        ],
        cwd=BACKEND_DIR,
        stdout=log_file,
        stderr=log_file,
    )

    try:
        wait_for_server()

        unique_email = f"ci-{uuid.uuid4().hex[:12]}@example.com"
        payload = json.dumps(
            {
                "name": "CI User",
                "email": unique_email,
                "password": "pwd123",
            }
        ).encode()

        request = urllib.request.Request(
            f"{BASE_URL}/api/register",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status != 201:
                    raise SystemExit(f"unexpected status {response.status}")
                data = json.loads(response.read().decode())
        except Exception as e:
            print("\n--- BACKEND LOGS (ERROR DIAGNOSTICS) ---")
            if Path("backend_smoke.log").exists():
                with open("backend_smoke.log", "r") as f:
                    print(f.read())
            print("--- END LOGS ---\n")
            raise e

        assert data["email"] == unique_email
        assert data["session"]["token"]
        return 0
    finally:
        process.terminate()
        log_file.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
