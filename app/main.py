"""Punto de entrada de la aplicación web."""

from app.app_factory import create_app, start_loop

app = create_app()
start_loop(app)
