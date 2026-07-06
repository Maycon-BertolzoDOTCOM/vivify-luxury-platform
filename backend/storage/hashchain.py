import sys
from pathlib import Path

SOC_PATH = Path(__file__).resolve().parent.parent.parent.parent / "soc"
sys.path.insert(0, str(SOC_PATH))

from soc.audit.hashchain import append, search, tail, verify_chain  # noqa: E402
from soc.audit import hashchain as hc_module  # noqa: E402

from ..config import AUDIT_DB_PATH


def patch_db_path() -> None:
    hc_module.DB_PATH = AUDIT_DB_PATH


def append_jewel_entry(
    event_type: str,
    jewel_id: str,
    metadata: dict,
) -> str:
    patch_db_path()
    return append(
        event_type=event_type,
        payload=metadata,
        db_path=AUDIT_DB_PATH,
        session_id=jewel_id,
        tenant_id="vivify",
    )


def get_jewel_chain(jewel_id: str, limit: int = 100) -> list:
    patch_db_path()
    result = search(
        session_id=jewel_id,
        tenant_id="vivify",
        limit=limit,
        db_path=AUDIT_DB_PATH,
    )
    return result.get("entries", [])


def get_chain_stats() -> dict:
    patch_db_path()
    result = search(tenant_id="vivify", limit=0)
    integrity = verify_chain(db_path=AUDIT_DB_PATH)
    return {
        "total": result.get("total", 0),
        "valid": integrity.get("valid", False),
    }
