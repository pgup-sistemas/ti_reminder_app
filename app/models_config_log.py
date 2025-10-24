"""Modelos auxiliares para auditoria de configurações."""

from __future__ import annotations

from datetime import datetime

from . import db
from .utils.timezone_utils import get_current_time_for_db


class ConfigChangeLog(db.Model):
    __tablename__ = "config_change_log"

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100), nullable=True)
    entity_id = db.Column(db.String(64), nullable=True)
    field = db.Column(db.String(100), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=get_current_time_for_db, nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    actor = db.relationship("User", backref=db.backref("config_change_logs", lazy=True))

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<ConfigChangeLog module={self.module} entity_type={self.entity_type} "
            f"entity_id={self.entity_id} field={self.field}>"
        )


class SecureConfig(db.Model):
    __tablename__ = "secure_config"

    key = db.Column(db.String(120), primary_key=True)
    value = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time_for_db, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=get_current_time_for_db,
        onupdate=get_current_time_for_db,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SecureConfig {self.key}>"
