"""
agent.py
Orchestrates: content_gen → voice_gen → video_gen → video_edit → output
Tracks progress in SQLite via SQLAlchemy. Resumes pending jobs on restart.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_ai.db import init_db, get_session, get_pending_job, VideoJob
from content_ai.content_gen import get_title, get_description, get_story, get_video_prompts
from audio_ai.voice_gen import VoiceGen
from vision_ai.video_gen import generate_video
from video_edit.video_edit import VideoEditor

ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR   = os.path.join(ROOT, "output")
SEGMENTS_DIR = os.path.join(ROOT, "temp", "video_segments")
VOICE_PATH   = os.path.join(ROOT, "temp", "content_voice.wav")
COMBINED_VID = os.path.join(ROOT, "temp", "content_video.mp4")
SPEAKER_WAV  = os.path.join(ROOT, "audio_ai", "voice_sample.wav")


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


def run(topic: str):
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
            print("\n[Agent] Step 1: Generating content...")
            job.title       = get_title(job.topic)
            job.description = get_description(job.topic)
            job.story       = get_story(job.topic)
            prompts         = get_video_prompts(job.topic)
            job.set_prompts(prompts)
            job.add_step("content")
            session.commit()
            print(f"[Agent] Title: {job.title}")
            print(f"[Agent] Story: {job.story[:80]}...")
            print(f"[Agent] Prompts: {len(prompts)} segments")
        else:
            print("\n[Agent] Step 1: content already done, skipping.")

        # ── Step 2: voice ────────────────────────────────────────────────────
        if not job.has_step("voice"):
            print("\n[Agent] Step 2: Generating voice...")
            vg = VoiceGen(speaker_wav=SPEAKER_WAV)
            vg.generate(job.story, output_path=VOICE_PATH)
            job.voice_path = VOICE_PATH
            job.add_step("voice")
            session.commit()
            print(f"[Agent] Voice ready: {VOICE_PATH}")
        else:
            print("\n[Agent] Step 2: voice already done, skipping.")

        # ── Step 3: video segments ───────────────────────────────────────────
        if not job.has_step("segments"):
            print("\n[Agent] Step 3: Generating video segments...")
            prompts       = job.get_prompts()
            segment_paths = []
            for i, prompt in enumerate(prompts):
                print(f"[Agent] Segment {i+1}/{len(prompts)}: {prompt[:60]}...")
                seg_path = generate_video(prompt)
                segment_paths.append(seg_path)
                print(f"[Agent] Segment {i+1} ready: {seg_path}")
            job.set_segments(segment_paths)
            job.add_step("segments")
            session.commit()
        else:
            print("\n[Agent] Step 3: segments already done, skipping.")

        # ── Step 4: combine segments ─────────────────────────────────────────
        if not job.has_step("combine"):
            print("\n[Agent] Step 4: Combining video segments...")
            editor = VideoEditor()
            editor.combine_segments(job.get_segments(), COMBINED_VID)
            job.add_step("combine")
            session.commit()
            print(f"[Agent] Combined: {COMBINED_VID}")
        else:
            print("\n[Agent] Step 4: combine already done, skipping.")

        # ── Step 5: merge video + voice ──────────────────────────────────────
        if not job.has_step("merge"):
            print("\n[Agent] Step 5: Merging video with voice...")
            editor = VideoEditor()
            # use title as filename, fallback to job id
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in job.title)
            safe_title = safe_title.strip().replace(" ", "_") or f"video_{job.id}"
            final_path = os.path.join(OUTPUT_DIR, f"{safe_title}.mp4")
            editor.combine(COMBINED_VID, VOICE_PATH, final_path)
            job.final_path = final_path
            job.add_step("merge")
            job.status = "done"
            session.commit()
            print(f"[Agent] Final video: {final_path}")
        else:
            print("\n[Agent] Step 5: merge already done, skipping.")

        # ── Cleanup ──────────────────────────────────────────────────────────
        for f in os.listdir(SEGMENTS_DIR):
            fp = os.path.join(SEGMENTS_DIR, f)
            if os.path.isfile(fp):
                os.remove(fp)
        print("[Agent] Cleaned up temp/video_segments/")

        print("\n" + "=" * 50)
        print(f"[Agent] Done. Final video: {job.final_path}")
        print("=" * 50)

        return job.final_path

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "a turtle exploring a magical pond"
    run(topic)
