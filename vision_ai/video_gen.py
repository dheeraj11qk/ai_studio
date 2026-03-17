import requests
import time
import subprocess
import os
import glob
import base64

SERVER = "http://localhost:5003"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEGMENTS_DIR = os.path.join(ROOT, "temp", "video_segments")
APP_BUNDLE   = os.path.join(ROOT, "meta_ai", "meta_ai_app.app")


def find_app_path() -> str:
    # prefer the bundled app in the project
    if os.path.isdir(APP_BUNDLE):
        return APP_BUNDLE
    # fallback to DerivedData
    pattern = os.path.expanduser(
        "~/Library/Developer/Xcode/DerivedData/meta_ai_app-*/Build/Products/Debug/meta_ai_app.app"
    )
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError("meta_ai_app.app not found. Run 'make build-app' first.")
    return max(matches, key=os.path.getmtime)


def is_server_running() -> bool:
    try:
        r = requests.get(f"{SERVER}/status", timeout=3)
        print(f"Server check: {r.status_code}")
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Server check: Connection refused")
        return False
    except requests.exceptions.Timeout:
        print("Server check: Timeout")
        return False
    except Exception as e:
        print(f"Server check: {e}")
        return False


def ensure_app_running():
    if is_server_running():
        print("App already running.")
        return

    # check if app bundle exists, build if not
    if not os.path.isdir(APP_BUNDLE):
        print(f"App bundle not found at {APP_BUNDLE}")
        print("Building app...")
        result = subprocess.run(["make", "build-app"], cwd=ROOT)
        if result.returncode != 0:
            raise RuntimeError("Failed to build app")

    print(f"Starting app: {APP_BUNDLE}")
    subprocess.Popen(["open", APP_BUNDLE])

    for i in range(60):  # increased from 30 to 60 seconds
        time.sleep(2)    # check every 2 seconds instead of 1
        if is_server_running():
            print(f"App started and server ready ({i*2}s)")
            return
        if i % 5 == 0:  # print status every 10 seconds
            print(f"Waiting for server... ({i*2}s)")

    raise RuntimeError("App launched but server did not respond on port 5003 after 120s")


def generate_video(prompt: str, timeout: int = 120) -> str:
    """
    Send prompt to Swift app, poll until video is ready,
    retrieve base64 data, save to temp/video_segments/, return path.
    """
    ensure_app_running()
    os.makedirs(SEGMENTS_DIR, exist_ok=True)

    resp = requests.post(f"{SERVER}/generate", json={"prompt": prompt}, timeout=10)
    resp.raise_for_status()
    print("Sent prompt:", resp.json())

    start = time.time()

    while True:
        elapsed = time.time() - start

        if elapsed > timeout:
            raise TimeoutError(f"Video not ready after {timeout}s")

        time.sleep(3)

        data = requests.get(f"{SERVER}/status", timeout=10).json()
        print(f"[{int(elapsed)}s] status:", data.get("status"))

        if data.get("status") == "completed":
            filename = data.get("filename", f"video_{int(time.time())}.mp4")
            b64 = data.get("data", "")

            # Decode and save to temp/video_segments/
            video_bytes = base64.b64decode(b64)
            out_path = os.path.join(SEGMENTS_DIR, filename)

            with open(out_path, "wb") as f:
                f.write(video_bytes)

            print("Video saved to:", out_path)

            # Clean up the file inside the app sandbox
            try:
                requests.post(f"{SERVER}/delete", timeout=5)
                print("Sandbox file deleted.")
            except Exception as e:
                print("Delete request failed (non-critical):", e)

            return out_path


if __name__ == "__main__":
    prompt = "Generate a cinematic video of a robot walking in a futuristic city"
    path = generate_video(prompt)
    print("Done. File saved at:", path)
