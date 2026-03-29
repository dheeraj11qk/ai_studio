"""
agent.py
Orchestrates: content_gen → voice_gen → video_gen → video_edit → output
Tracks progress in SQLite via SQLAlchemy. Resumes pending jobs on restart.
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_ai.db import init_db, get_session, get_pending_job, VideoJob
from content_ai.main import ContentGenAI
from audio_ai.main import Audio_AI
from network_media.main import NetworkMedia
from quick_board_ai.main import QuickBoardAI
import shutil
import subprocess

ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR   = os.path.join(ROOT, "output")
SEGMENTS_DIR = os.path.join(ROOT, "temp", "video_segments")
VOICE_PATH   = os.path.join(ROOT, "audio_ai", "output", "voice.wav")
SPEAKER_WAV  = "voice_sample.wav"


def _ask_resume(job: VideoJob) -> bool:
    pending = job.pending_steps()
    done    = job.get_steps()
    print("\n" + "=" * 50)
    print(f"[Agent] Found pending job (id={job.id})")
    print(f"  Topic   : {job.topic}")
    print(f"  Done    : {done if done else 'nothing yet'}")
    print(f"  Pending : {pending}")
    print("=" * 50)
    ans = input("Resume last video? [y/n]: ").strip().lower()
    return ans == "y"


def run(topic: str, duration: str = "5 sec", lang: str = "en", quickboard: str = "false", character: str = "communicator", mode: str = "landscape"):
    init_db()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SEGMENTS_DIR, exist_ok=True)

    session = get_session()

    try:
        # ── Check for pending job ────────────────────────────────────────────
        pending_job = (
            session.query(VideoJob)
            .filter(VideoJob.status == "pending")
            .order_by(VideoJob.updated_at.desc())
            .first()
        )

        if pending_job and _ask_resume(pending_job):
            job = pending_job
            print(f"\n[Agent] Resuming job id={job.id}: {job.topic}")
        else:
            job = VideoJob(topic=topic, status="pending")
            session.add(job)
            session.commit()
            print(f"\n[Agent] New job id={job.id}: {topic}")

        print("=" * 50)

        # ── Step 1: content ──────────────────────────────────────────────────
        if not job.has_step("content"):
            print(f"\n[Agent] Step 1: Generating content ({lang}) | Character: {character}...")
            content_ai = ContentGenAI()
            data = content_ai.generate(job.topic, duration_str=duration, lang=lang, character=character)
            
            if data:
                job.title = data.get("title", "Untitled")
                job.story = data.get("description", "")
                job.add_step("content")
                session.commit()
                print(f"[Agent] Title: {job.title}")
            else:
                print("[Agent] ❌ Error: Content generation failed.")
                return
        else:
            print("\n[Agent] Step 1: content already done, skipping.")

        # Load content.json for subsequent steps
        content_path = os.path.join(ROOT, "content_ai", "json", "content.json")
        with open(content_path) as f:
            content_data = json.load(f)

        # ── Step 2: voice ────────────────────────────────────────────────────
        if not job.has_step("voice"):
            print(f"\n[Agent] Step 2: Generating voiceover ({lang}) using Audio_AI...")
            voice_track = content_data.get("tracks", {}).get("voice", [])
            # Map hinglish to hi for XTTS model
            audio_lang = "hi" if lang.lower() == "hinglish" else lang
            audio_ai = Audio_AI(speaker_wav=SPEAKER_WAV, language=audio_lang)
            audio_ai.generate_voice(voice_track, output_path=VOICE_PATH)
            job.voice_path = VOICE_PATH
            job.add_step("voice")
            session.commit()
            print(f"[Agent] Voice ready: {VOICE_PATH}")
        else:
            print("\n[Agent] Step 2: voice already done, skipping.")

        # ── Step 3: video segments (The Intelligent Fallback) ─────────────────
        if not job.has_step("segments"):
            print(f"\n[Agent] Step 3: Generating video segments (Mode: {mode.upper()} | Type: {'QuickBoard' if quickboard == 'true' else 'Dynamic'})...")
            visuals = content_data.get("tracks", {}).get("visuals", [])
            media = NetworkMedia()
            qb = QuickBoardAI()
            
            # Setup Aspect Ratio Filters
            if mode.lower() == "portrait":
                res_filter = 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setdar=9/16'
            else:
                res_filter = 'scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setdar=16/9'

            segment_paths = []
            for i, vis in enumerate(visuals):
                keyword = vis.get("search_key_word", vis.get("description", ""))
                desc = vis.get("description", "")
                v_duration = vis.get("duration", 5.0)
                seg_dest = os.path.abspath(os.path.join(SEGMENTS_DIR, f"seg_{i}.mp4"))
                
                print(f"\n[Agent] Processing Segment {i+1}/{len(visuals)}: '{keyword}'")
                
                success = False
                is_quickboard_only = (quickboard.lower() == "true")

                if not is_quickboard_only:
                    # FALLBACK 1: Pexels Video
                    print(f"[Agent] [F1] Trying Pexels Video...")
                    vid_url = media.getVideo(keyword)
                    if vid_url:
                        local_vid = media.downloadVideo(keyword)
                        if local_vid:
                            # Standardize using Smart-Crop
                            cmd = f'ffmpeg -y -i "{local_vid}" -t {v_duration} -vf "{res_filter}" -c:v libx264 -pix_fmt yuv420p "{seg_dest}"'
                            subprocess.run(cmd, shell=True)
                            print(f"[Agent] ✅ F1 Success: Video saved to {seg_dest}")
                            success = True

                    # FALLBACK 2: Pexels Image
                    if not success:
                        print(f"[Agent] [F2] Trying Pexels Image...")
                        img_url = media.getImage(keyword)
                        if img_url:
                            local_img = media.downloadImage(keyword)
                            if local_img:
                                # Convert image to video using Smart-Crop
                                cmd = f'ffmpeg -y -loop 1 -i "{local_img}" -t {v_duration} -vf "{res_filter}" -c:v libx264 -pix_fmt yuv420p "{seg_dest}"'
                                subprocess.run(cmd, shell=True)
                                print(f"[Agent] ✅ F2 Success: Image-Video saved to {seg_dest}")
                                success = True
                
                # FALLBACK 3: QuickBoard AI
                if not success:
                    print(f"[Agent] [F3] {'Forcing' if is_quickboard_only else 'Falling back to'} QuickBoard AI...")
                    qb_output = qb.gen_video(desc)
                    if qb_output:
                        # QuickBoard might need its own resize if not already matched
                        cmd = f'ffmpeg -y -i "{qb_output}" -t {v_duration} -vf "{res_filter}" -c:v libx264 -pix_fmt yuv420p "{seg_dest}"'
                        subprocess.run(cmd, shell=True)
                        print(f"[Agent] ✅ F3 Success: Video saved to {seg_dest}")
                        success = True

                if success:
                    segment_paths.append(seg_dest)
                else:
                    print(f"[Agent] ❌ Error: All fallbacks failed for segment {i+1}")

            job.set_segments(segment_paths)
            job.add_step("segments")
            session.commit()
        else:
            print("\n[Agent] Step 3: segments already done, skipping.")

        # ── Step 4: combine segments ────────────────────────────────────────
        combined_video = os.path.join(ROOT, "temp", "combined_video.mp4")
        if not job.has_step("combine"):
            print("\n[Agent] Step 4: Combining video segments...")
            segments = job.get_segments()
            if not segments:
                print("[Agent] ❌ Error: No segments to combine.")
                return
            
            # Create concat list
            list_path = os.path.join(ROOT, "temp", "segments.txt")
            with open(list_path, "w") as f:
                for s in segments:
                    f.write(f"file '{s}'\n")
            
            # Concat with ffmpeg
            cmd = f"ffmpeg -y -f concat -safe 0 -i {list_path} -c copy {combined_video}"
            subprocess.run(cmd, shell=True)
            
            job.add_step("combine")
            session.commit()
            print(f"[Agent] Combined: {combined_video}")
        else:
            print("\n[Agent] Step 4: combine already done, skipping.")

        # ── Step 5: Master Merge (Video + Master Audio Mix) ──────────────────
        if not job.has_step("merge"):
            print(f"\n[Agent] Step 5: Merging with Master Audio Mix ({lang})...")
            # Map hinglish to hi for XTTS model
            audio_lang = "hi" if lang.lower() == "hinglish" else lang
            audio_ai = Audio_AI(speaker_wav=SPEAKER_WAV, language=audio_lang)
            master_audio = audio_ai.generate_master_mix(content_data.get("tracks", {}))
            
            if not master_audio:
                print("[Agent] ❌ Error: Master audio mix failed.")
                return

            # Cleanup title for filename
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in job.title)
            safe_title = safe_title.strip().replace(" ", "_") or f"video_{job.id}"
            final_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"{safe_title}.mp4"))
            
            # Final Merge: Video + Master Audio
            cmd = f'ffmpeg -y -i "{combined_video}" -i "{master_audio}" -c:v copy -c:a aac -shortest "{final_path}"'
            subprocess.run(cmd, shell=True)
            
            job.final_path = final_path
            job.add_step("merge")
            job.status = "done"
            session.commit()
            print(f"\n[Agent] 🎉 SUCCESS! FINAL VIDEO READY: {final_path}")
        else:
            print("\n[Agent] Step 5: merge already done, skipping.")

        # ── FINAL CLEANUP ───────────────────────────────────────────────────
        print("\n[Agent] Cleaning up production files...")
        # Clean segments
        for f in os.listdir(SEGMENTS_DIR):
            fp = os.path.join(SEGMENTS_DIR, f)
            if os.path.isfile(fp):
                os.remove(fp)
        
        # Clean temp files
        temp_files = [os.path.join(ROOT, "temp", "segments.txt"), combined_video]
        for tf in temp_files:
            if os.path.exists(tf):
                os.remove(tf)
                
        print("[Agent] Cleanup complete. ✨")

        print("\n" + "=" * 50)
        print(f"[Agent] PRODUCTION COMPLETE: {job.title}")
        print("=" * 50)

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "a turtle exploring a magical pond"
    duration = sys.argv[2] if len(sys.argv) > 2 else "5 sec"
    lang = sys.argv[3] if len(sys.argv) > 3 else "en"
    qb_mode = sys.argv[4] if len(sys.argv) > 4 else "false"
    char_mode = sys.argv[5] if len(sys.argv) > 5 else "communicator"
    view_mode = sys.argv[6] if len(sys.argv) > 6 else "landscape"
    run(topic, duration, lang, qb_mode, char_mode, view_mode)
