"""每个 session_id 一个子进程，命名空间在该进程内保持。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

_WORKER = Path(__file__).with_name("worker_main.py")


class SessionWorker:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.process = self._spawn()
        self.lock = threading.Lock()

    def _spawn(self) -> subprocess.Popen[str]:
        env = os.environ.copy()
        src = Path(__file__).resolve().parents[2]
        env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.Popen(
            [sys.executable, str(_WORKER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def execute(self, code: str, timeout: float | None = None) -> dict[str, str | bool]:
        with self.lock:
            if self.process.poll() is not None:
                self.process = self._spawn()
            assert self.process.stdin and self.process.stdout
            payload = json.dumps({"op": "exec", "code": code}, ensure_ascii=False)
            self.process.stdin.write(payload + "\n")
            self.process.stdin.flush()
            line = self._read(timeout)
            if line is None:
                self.cancel()
                return {
                    "ok": False,
                    "stdout": "",
                    "error": "执行已取消或超时。工作进程已重建，本次调用之前的未序列化对象不会保留。",
                }
            if not line.strip():
                error = ""
                if self.process.stderr is not None and self.process.poll() is not None:
                    error = self.process.stderr.read()
                self.process = self._spawn()
                return {"ok": False, "stdout": "", "error": error or "工作进程在返回结果前退出。"}
            return json.loads(line)

    def _read(self, timeout: float | None) -> str | None:
        holder: dict[str, str] = {}

        def _target() -> None:
            assert self.process.stdout
            holder["line"] = self.process.stdout.readline()

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            return None
        line = holder.get("line", "")
        return line if line else None

    def cancel(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process = self._spawn()


class WorkerPool:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionWorker] = {}
        self.lock = threading.Lock()

    def get(self, session_id: str) -> SessionWorker:
        with self.lock:
            worker = self.sessions.get(session_id)
            if worker is None:
                worker = SessionWorker(session_id)
                self.sessions[session_id] = worker
            return worker
