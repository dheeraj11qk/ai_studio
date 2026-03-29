import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# API setup
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeManager:
    """
    Handles authentication and video uploads to YouTube via Google API.
    Requires client_secret.json in the root directory.
    """
    
    def __init__(self, secrets_file="client_secret.json"):
        self.secrets_file = secrets_file
        self.credentials = None
        self.youtube = None

    def authenticate(self):
        """Authenticates the user and builds the YouTube service."""
        print("[YouTube] Authenticating...")
        if not os.path.exists(self.secrets_file):
            raise FileNotFoundError(f"Missing '{self.secrets_file}'. Please download it from Google Cloud Console.")
            
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.secrets_file, SCOPES
        )
        self.credentials = flow.run_local_server(port=0) # Use local server for easier auth flow
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=self.credentials
        )
        print("[YouTube] Authentication successful! ✅")

    def upload_video(self, video_path, title, description, tags=None, category_id="22", privacy="private"):
        """Performs the video upload."""
        if not self.youtube:
            self.authenticate()

        print(f"[YouTube] Starting upload: {video_path}")
        
        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or ["AI", "automation", "python"],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        request = self.youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[YouTube] Upload Progress: {int(status.progress() * 100)}%")

        print(f"[YouTube] 🎉 UPLOAD COMPLETE! Video ID: {response['id']}")
        return response["id"]

if __name__ == "__main__":
    # Test block
    try:
        uploader = YouTubeManager()
        # uploader.upload_video("test.mp4", "Test AI Video", "Automated upload test")
    except Exception as e:
        print(f"[YouTube] Error: {e}")
