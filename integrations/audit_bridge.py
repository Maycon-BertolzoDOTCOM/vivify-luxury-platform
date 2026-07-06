import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("vivify.integrations.audit_bridge")

AUDIT_DB_PATH = os.getenv(
    "AUDIT_CHAIN_DB",
    str(Path(__file__).resolve().parent.parent.parent / "memory" / "audit_chain.db"),
)


def _import_hashchain():
    sys.path.insert(
        0,
        str(Path(__file__).resolve().parent.parent.parent / "soc"),
    )
    from soc.audit import hashchain as hc_module
    from soc.audit.hashchain import append, search, verify_chain

    hc_module.DB_PATH = AUDIT_DB_PATH
    return append, search, verify_chain


class AuditBridge:
    def __init__(self, tenant: str = "vivify"):
        self.tenant = tenant
        self._append_fn = None
        self._search_fn = None
        self._verify_fn = None

    def _lazy_init(self):
        if self._append_fn is None:
            append, search, verify = _import_hashchain()
            self._append_fn = append
            self._search_fn = search
            self._verify_fn = verify

    def log_action(
        self,
        action: str,
        target: str = "",
        agent: str = "",
        metadata: dict | None = None,
        status: str = "completed",
    ) -> dict:
        self._lazy_init()
        payload = {
            "action": action,
            "target": target,
            "agent": agent,
            "status": status,
            "metadata": metadata or {},
            "_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            entry_hash = self._append_fn(
                event_type=f"vivify.camel.{action}",
                payload=payload,
                db_path=AUDIT_DB_PATH,
                session_id=target or "camel_agent",
                tenant_id=self.tenant,
            )
            logger.info(
                "Audit logged: %s -> %s (hash: %s...)",
                action, target or "(global)", entry_hash[:12],
            )
            return {"success": True, "hash": entry_hash}
        except Exception as e:
            logger.warning("Audit failed (non-critical): %s", e)
            return {"success": False, "error": str(e)}

    def query_actions(
        self,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list:
        self._lazy_init()
        result = self._search_fn(
            session_id=session_id,
            tenant_id=self.tenant,
            limit=limit,
            db_path=AUDIT_DB_PATH,
        )
        return result.get("entries", [])

    def verify_integrity(self) -> dict:
        self._lazy_init()
        return self._verify_fn(db_path=AUDIT_DB_PATH)
