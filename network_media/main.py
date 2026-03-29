import os
import requests
from dotenv import load_dotenv

# =========================
# CONFIGURATION
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETWORK_MEDIA_DIR = os.path.join(BASE_DIR, "network_media")
DOWNLOADS_DIR = os.path.join(NETWORK_MEDIA_DIR, "downloads")
load_dotenv(os.path.join(BASE_DIR, ".env"))

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

class NetworkMedia:
    """
    Gateway to fetch and download high-quality images and videos from Pexels API.
    """

    def __init__(self):
        if not PEXELS_API_KEY:
            print("[NetworkMedia] ⚠️ WARNING: PEXELS_API_KEY not found in .env")
        self.headers = {"Authorization": PEXELS_API_KEY}
        self.img_base_url = "https://api.pexels.com/v1/search"
        self.vid_base_url = "https://api.pexels.com/videos/search"
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    def _download(self, url: str, filename: str) -> str:
        """Helper to download a file from a URL and return the local path."""
        path = os.path.join(DOWNLOADS_DIR, filename)
        print(f"[NetworkMedia] Downloading to {path}...")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[NetworkMedia] ✅ Success! Saved to {path}")
            return path
        except Exception as e:
            print(f"[NetworkMedia] ❌ ERROR: Download failed ({e})")
            return None

    def getImage(self, query: str, per_page: int = 1) -> str:
        """Fetches a single high-quality image URL based on the query."""
        print(f"[NetworkMedia] Searching image for: '{query}'...")
        params = {"query": query, "per_page": per_page}
        try:
            response = requests.get(self.img_base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            photos = data.get("photos", [])
            if photos:
                return photos[0].get("src", {}).get("original")
            else:
                print(f"[NetworkMedia] ❌ No photos found for '{query}'")
                return None
        except Exception as e:
            print(f"[NetworkMedia] ❌ Error fetching image URL: {e}")
            return None

    def getVideo(self, query: str, per_page: int = 1) -> str:
        """Fetches a single high-quality video URL based on the query."""
        print(f"[NetworkMedia] Searching video for: '{query}'...")
        params = {"query": query, "per_page": per_page}
        try:
            response = requests.get(self.vid_base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            videos = data.get("videos", [])
            if videos:
                video_files = videos[0].get("video_files", [])
                if video_files:
                    return video_files[0].get("link")
            print(f"[NetworkMedia] ❌ No videos found for '{query}'")
            return None
        except Exception as e:
            print(f"[NetworkMedia] ❌ Error fetching video URL: {e}")
            return None

    def downloadImage(self, query: str) -> str:
        """Searches, downloads, and returns the path to a high-quality image."""
        url = self.getImage(query)
        if url:
            # Generate filename from query (safe)
            safe_name = "".join([c if c.isalnum() else "_" for c in query]).strip("_")
            filename = f"img_{safe_name}_{os.urandom(4).hex()}.jpeg"
            return self._download(url, filename)
        return None

    def downloadVideo(self, query: str) -> str:
        """Searches, downloads, and returns the path to a high-quality video."""
        url = self.getVideo(query)
        if url:
            # Generate filename from query (safe)
            safe_name = "".join([c if c.isalnum() else "_" for c in query]).strip("_")
            filename = f"vid_{safe_name}_{os.urandom(4).hex()}.mp4"
            return self._download(url, filename)
        else:
            print(f"[NetworkMedia] ❌ video download search when not found say no")
            return None

# =========================
# CLI TEST ENTRY POINT
# =========================
if __name__ == "__main__":
    net = NetworkMedia()
    
    # Example Download Test
    img_path = net.downloadImage("lonely robot on mars")
    vid_path = net.downloadVideo("martian landscape sunset")
    
    print("\n--- DOWNLOAD RESULTS ---")
    print(f"IMAGE PATH: {img_path}")
    print(f"VIDEO PATH: {vid_path}")
