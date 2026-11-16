"""Background render queue for the Vāgdhenu demo.

One worker thread renders jobs one at a time (an 8 GB Mac only fits one model run), so the page
stays free: you can queue the next verse, open finished chants, or record a video meanwhile.
Jobs are persisted to out/queue/jobs.json — finished chants survive a restart and unfinished
ones are resumed.
"""
import json
import os
import threading
import time
import uuid

import numpy as np
import soundfile as sf

ACTIVE = ("queued", "rendering")


class RenderQueue:
    def __init__(self, render_fn, finish_fn, state_dir, log=print):
        """render_fn(text, meter, seed, progress_cb) -> (sr, audio, meters, timestamps)
        finish_fn(dry_audio, sr, job, timestamps) -> (final_audio, timestamps, sa) — bells, tanpura."""
        self.render_fn, self.finish_fn, self.log = render_fn, finish_fn, log
        self.dir = state_dir
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "jobs.json")
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.jobs = {}  # id -> dict (insertion order = submission order)
        self._load()
        threading.Thread(target=self._worker, name="vagdhenu-render", daemon=True).start()

    # ── persistence ──────────────────────────────────────────────────
    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                for j in json.load(f):
                    if j.get("status") == "rendering":
                        j.update(status="queued", progress=0.0, desc="Waiting (resumed after restart)")
                    self.jobs[j["id"]] = j
        except FileNotFoundError:
            pass
        except Exception as e:
            self.log(f"[queue] could not read {self.path}: {e}", flush=True)

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(list(self.jobs.values()), f, ensure_ascii=False)
        os.replace(tmp, self.path)

    # ── API ──────────────────────────────────────────────────────────
    def submit(self, text, meter, seed, tanpura_on, tanpura_level, bell="off", title=None):
        snippet = title or next((ln.strip() for ln in text.splitlines() if ln.strip()), text.strip())
        job = {
            "id": uuid.uuid4().hex[:10], "created": time.time(), "text": text, "meter": meter,
            "seed": int(seed), "tanpura_on": bool(tanpura_on), "tanpura_level": float(tanpura_level),
            "bell": bell or "off", "snippet": (snippet[:60] + "…") if len(snippet) > 61 else snippet,
            "status": "queued", "progress": 0.0, "desc": "Waiting", "error": None, "result": None,
        }
        with self.lock:
            self.jobs[job["id"]] = job
            self._save()
        self.wake.set()
        return dict(job)

    def get(self, job_id):
        with self.lock:
            j = self.jobs.get(job_id)
            return dict(j) if j else None

    def list(self):
        with self.lock:
            return [dict(j) for j in self.jobs.values()]

    def position(self, job_id):
        with self.lock:
            q = [j["id"] for j in self.jobs.values() if j["status"] in ACTIVE]
        return q.index(job_id) if job_id in q else -1

    def cancel(self, job_id):
        with self.lock:
            j = self.jobs.get(job_id)
            if j and j["status"] == "queued":
                j.update(status="cancelled", desc="Cancelled")
                self._save()
                return True
        return False

    def remove(self, job_id):
        with self.lock:
            j = self.jobs.get(job_id)
            if j and j["status"] not in ACTIVE:
                del self.jobs[job_id]
                self._save()
                return True
        return False

    def clear_finished(self):
        with self.lock:
            for k in [k for k, j in self.jobs.items() if j["status"] not in ACTIVE]:
                del self.jobs[k]
            self._save()

    # ── worker ───────────────────────────────────────────────────────
    def _next(self):
        with self.lock:
            return next((j for j in self.jobs.values() if j["status"] == "queued"), None)

    def _update(self, job, **kw):
        with self.lock:
            job.update(kw)

    def _worker(self):
        while True:
            job = self._next()
            if job is None:
                self.wake.wait(timeout=2.0)
                self.wake.clear()
                continue
            self._update(job, status="rendering", progress=0.0, desc="Starting…", started=time.time())
            try:
                def progress_cb(frac, desc):
                    self._update(job, progress=float(max(0.0, min(1.0, frac))), desc=str(desc))

                sr, audio, meters, stamps = self.render_fn(job["text"], job["meter"], job["seed"], progress_cb)
                dry = np.asarray(audio, np.float32)
                stamp = int(time.time() * 1000)
                dry_path = os.path.join(self.dir, f"dry_{job['id']}.wav")
                sf.write(dry_path, dry, sr)
                final, final_stamps, sa = self.finish_fn(dry, sr, job, stamps)
                wav_path = os.path.abspath(os.path.join(self.dir, "..", "chants", f"chant_{stamp}.wav"))
                os.makedirs(os.path.dirname(wav_path), exist_ok=True)
                sf.write(wav_path, final, sr)
                result = {"wav": wav_path, "dry": dry_path, "sr": sr, "sa": sa, "meters": list(meters),
                          "timestamps": final_stamps, "dry_timestamps": stamps, "dur": len(final) / sr}
                with self.lock:
                    job.update(status="done", progress=1.0, desc="Ready", result=result, finished=time.time())
                    self._save()
                self.log(f"[queue] {job['id']} done: {result['dur']:.1f}s audio in "
                         f"{job['finished'] - job['started']:.0f}s", flush=True)
            except Exception as e:  # keep the worker alive for the next job
                self.log(f"[queue] {job['id']} failed: {e}", flush=True)
                with self.lock:
                    job.update(status="failed", desc="Failed", error=str(e))
                    self._save()
