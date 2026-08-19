from __future__ import annotations

import threading

from app.pqi.engine import PQIEngine
from app.pqi.state import PQIState
from app.models.pqi_session import PQISession


class PQIRuntimeManager:
    """Owns one independent PQIEngine/PQIState per persistent session."""

    def __init__(self):
        self._lock = threading.RLock()
        self._engines = {}

    def get(self, session_id):
        with self._lock:
            return self._engines.get(str(session_id))

    def ensure(self, session_obj, app=None, user_id=None):
        sid = str(session_obj.id)
        with self._lock:
            runtime = self._engines.get(sid)
            if runtime is None:
                runtime = PQIEngine(state=PQIState())
                self._engines[sid] = runtime
                runtime.restore_user_session(user_id or session_obj.user_id, app=app, session_id=session_obj.id)
            elif not (runtime._thread and runtime._thread.is_alive()):
                runtime.restore_user_session(user_id or session_obj.user_id, app=app, session_id=session_obj.id)
            return runtime

    def ensure_user(self, user_id, app=None):
        sessions = (
            PQISession.query
            .filter_by(user_id=user_id, status="ACTIVE")
            .order_by(PQISession.started_at.desc())
            .all()
        )
        return [self.ensure(s, app=app, user_id=user_id) for s in sessions]

    def remove(self, session_id):
        with self._lock:
            return self._engines.pop(str(session_id), None)


runtime_manager = PQIRuntimeManager()
