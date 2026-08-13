import os
import sys
import io
import socket
import subprocess
import threading
import time

# Ensure stdout and stderr handle UTF-8 symbols gracefully on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def stream_output(process, prefix):
    """Stream stdout/stderr of a child process line-by-line with a tagged prefix."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"{prefix} {line.strip()}", flush=True)
    except (ValueError, Exception):
        pass

def wait_for_backend_ready(host="127.0.0.1", port=8000, timeout=20):
    """Poll backend port until it is open and accepting socket connections."""
    start_time = time.time()
    print(f"⏳ Waiting for Backend server to become ready on http://{host}:{port}...", flush=True)
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print("✅ Backend server is live and accepting API requests!", flush=True)
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.4)
    print("⚠️ Backend server startup timeout. Proceeding with frontend launch...", flush=True)
    return False

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    print("=" * 75)
    print("🚀 Starting AI-Powered Data Quality Platform (Synced Dual Server)...")
    print("=" * 75)

    # Determine Python executable
    if sys.platform == "win32":
        venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
        npm_cmd = "npm.cmd"
    else:
        venv_python = os.path.join(backend_dir, "venv", "bin", "python")
        npm_cmd = "npm"

    python_bin = venv_python if os.path.exists(venv_python) else sys.executable
    print(f"🐍 Python Executable : {python_bin}")
    print(f"⚙️  Backend Directory : {backend_dir}")
    print(f"📦 Frontend Directory: {frontend_dir}")
    print("-" * 75)

    processes = []

    try:
        # 1. Start Backend Process (FastAPI / Uvicorn)
        print("\n[1/2] 🔌 Launching Backend FastAPI Server (Port 8000)...")
        backend_cmd = [
            python_bin, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        ]
        
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        processes.append(backend_process)

        t_backend = threading.Thread(target=stream_output, args=(backend_process, "[Backend]"))
        t_backend.daemon = True
        t_backend.start()

        # Wait until Backend socket port 8000 is open before launching Frontend
        wait_for_backend_ready("127.0.0.1", 8000, timeout=20)

        # 2. Start Frontend Process (React / Vite)
        print("\n[2/2] 💻 Launching Frontend Vite Dev Server (Port 3000 / 5173)...")
        frontend_cmd = [npm_cmd, "run", "dev"]
        
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=(sys.platform == "win32")
        )
        processes.append(frontend_process)

        t_frontend = threading.Thread(target=stream_output, args=(frontend_process, "[Frontend]"))
        t_frontend.daemon = True
        t_frontend.start()

        print("\n" + "=" * 75)
        print("✅ Startup Complete! Both services are synchronized and live:")
        print("   • Backend API Gateway: http://127.0.0.1:8000")
        print("   • Interactive API Docs: http://127.0.0.1:8000/docs")
        print("   • Frontend Dashboard:   http://localhost:3000")
        print("   👉 Press Ctrl+C at any time to stop both servers simultaneously.")
        print("=" * 75 + "\n")

        # Synchronized Health Monitor: If ANY server dies or stops, shut down both!
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print("\n⚠️ A server process stopped unexpectedly. Shutting down both services...", flush=True)
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received. Terminating both Backend & Frontend services...")
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("✨ Both Backend and Frontend servers shut down cleanly. Goodbye!")

if __name__ == "__main__":
    main()
