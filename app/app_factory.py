"""Fábrica de la aplicación FastAPI."""

from __future__ import annotations

import logging
import threading
from datetime import timezone
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.adapters.clocks import SimulatedClock, SystemClock
from app.adapters.fake_calendar import FakeCalendar
from app.adapters.sim_messaging import SimulatedMessaging
from app.config import Config
from app.db.repository import connect
from app.demo_seed import reset_demo
from app.services.planner import run_cycle
from app.web.routes import router as panel_router
from app.web.sim_routes import router as sim_router
from app.web.agenda_routes import router as agenda_router
from app.web.waitlist_routes import router as waitlist_router

logger = logging.getLogger(__name__)

_PLANNER_INTERVAL_SECONDS = 60


def create_app(config: Config | None = None) -> FastAPI:
    """Crea la aplicación con los adaptadores según el modo."""
    config = config or Config.from_env()
    repo = connect(config.database_path)
    clinic_tz = (
        ZoneInfo(config.clinic_timezone) if config.clinic_timezone else timezone.utc
    )

    app = FastAPI(title="Recordatorios — Consultorio de la Dra. Laura")
    app.state.repo = repo
    app.state.clinic_tz = clinic_tz
    app.state.mode = config.mode

    if config.is_demo:
        app.state.calendar = FakeCalendar()
        app.state.messaging = SimulatedMessaging()
        app.state.clock = SimulatedClock()
        reset_demo(
            repo,
            app.state.calendar,
            app.state.clock,
            app.state.messaging,
            clinic_tz=clinic_tz,
        )
        app.include_router(sim_router)
        app.include_router(agenda_router)
        app.include_router(waitlist_router)
    else:
        app.state.calendar = None
        app.state.messaging = None
        app.state.clock = SystemClock()

    app.include_router(panel_router)
    app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def start_loop(app: FastAPI) -> threading.Thread | None:
    """Arranca el planificador de fondo (sincroniza y envía cada minuto)."""
    if app.state.mode != "demo":
        return None

    stop = threading.Event()

    def loop() -> None:
        while not stop.is_set():
            try:
                run_cycle(
                    app.state.calendar,
                    app.state.repo,
                    app.state.messaging,
                    app.state.clock,
                    clinic_tz=app.state.clinic_tz,
                )
            except Exception:
                logger.exception("ciclo del planificador falló")
            stop.wait(_PLANNER_INTERVAL_SECONDS)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread
