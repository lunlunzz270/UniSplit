"""Core database helpers for UniSplit."""

from .database import Base, SessionLocal, engine, get_db


def init_db(app):
    """Backwards-compatible stub for older startup code."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unisplit.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
