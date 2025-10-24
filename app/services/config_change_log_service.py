"""Serviço utilitário para registrar auditoria de configurações."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from flask import current_app

from .. import db
from ..models import ConfigChangeLog


@dataclass
class ChangeDescriptor:
    module: str
    actor_id: Optional[int]
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class ConfigChangeLogService:
    """Interface de alto nível para persistir logs de configuração."""

    @staticmethod
    def register_change(
        descriptor: ChangeDescriptor,
        field: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConfigChangeLog:
        if not descriptor.module:
            raise ValueError("descriptor.module é obrigatório")

        log_entry = ConfigChangeLog(
            module=descriptor.module,
            entity_type=descriptor.entity_type,
            entity_id=str(descriptor.entity_id) if descriptor.entity_id is not None else None,
            field=field,
            old_value=_serialize_value(old_value),
            new_value=_serialize_value(new_value),
            audit_metadata=metadata,
            actor_id=descriptor.actor_id,
        )

        db.session.add(log_entry)

        try:
            db.session.commit()
            current_app.logger.info(
                "ConfigChangeLog registrado",
                extra={
                    "module": descriptor.module,
                    "entity_type": descriptor.entity_type,
                    "entity_id": descriptor.entity_id,
                    "field": field,
                    "actor_id": descriptor.actor_id,
                },
            )
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Falha ao registrar ConfigChangeLog")
            raise

        return log_entry

    @staticmethod
    def register_bulk_changes(
        descriptor: ChangeDescriptor,
        changes: Iterable[Dict[str, Any]],
    ) -> None:
        for entry in changes:
            ConfigChangeLogService.register_change(
                descriptor=descriptor,
                field=entry.get("field"),
                old_value=entry.get("old_value"),
                new_value=entry.get("new_value"),
                metadata=entry.get("metadata"),
            )


def _serialize_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return str(value)
