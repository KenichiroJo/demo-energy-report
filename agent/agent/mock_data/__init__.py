import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent


def _load(name: str) -> list | dict:
    with open(_DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_financial_data() -> list[dict]:
    return _load("financial.json")


def load_sfa_data() -> list[dict]:
    return _load("sfa.json")


def load_documents_data() -> list[dict]:
    return _load("documents.json")
