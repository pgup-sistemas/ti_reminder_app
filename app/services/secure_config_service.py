"""Serviço para gerenciamento seguro de segredos de configuração."""

from __future__ import annotations

from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

from .. import db
from ..models import SecureConfig


class SecureConfigUnavailable(RuntimeError):
    """Indica que a camada de criptografia não está disponível."""


class SecureConfigService:
    @staticmethod
    def _get_cipher() -> Fernet:
        raw_key = current_app.config.get("CONFIG_SECRET_KEY")
        if not raw_key:
            raise SecureConfigUnavailable(
                "CONFIG_SECRET_KEY não configurada. Defina uma chave Fernet válida no ambiente."
            )

        if isinstance(raw_key, str):
            key_bytes = raw_key.encode("utf-8")
        else:
            key_bytes = raw_key

        try:
            return Fernet(key_bytes)
        except (ValueError, TypeError) as exc:
            raise SecureConfigUnavailable(
                "CONFIG_SECRET_KEY inválida. Gere uma chave com `python -m cryptography.fernet`"
            ) from exc

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    @staticmethod
    def set_secret(key: str, value: Any) -> None:
        if value is None or value == "":
            SecureConfigService.delete_secret(key)
            return

        cipher = SecureConfigService._get_cipher()
        payload = str(value).encode("utf-8")
        encrypted = cipher.encrypt(payload)

        record = SecureConfig.query.get(key)
        if record:
            record.value = encrypted
        else:
            db.session.add(SecureConfig(key=key, value=encrypted))

        db.session.commit()

    @staticmethod
    def get_secret(key: str, default: Optional[Any] = None) -> Optional[str]:
        record = SecureConfig.query.get(key)
        if not record:
            return default

        cipher = SecureConfigService._get_cipher()
        try:
            decrypted = cipher.decrypt(record.value)
        except InvalidToken as exc:
            raise SecureConfigUnavailable(
                "Não foi possível descriptografar o segredo armazenado."
            ) from exc
        return decrypted.decode("utf-8")

    @staticmethod
    def delete_secret(key: str) -> None:
        record = SecureConfig.query.get(key)
        if not record:
            return
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def has_secret(key: str) -> bool:
        return SecureConfig.query.get(key) is not None

    @staticmethod
    def ensure_available() -> None:
        SecureConfigService._get_cipher()
