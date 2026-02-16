from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    async def log(session, user_id: int, action: str, entity: str, entity_id: int, description: str | None = None) -> None:
        session.add(AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            description=description,
        ))
