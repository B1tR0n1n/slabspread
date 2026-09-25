import json
import os

os.environ.setdefault("SLABSPREAD_AUTH_MODE", "off")
os.environ.setdefault("SLABSPREAD_DEBUG", "1")
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "fixtures"


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine, expire_on_commit=False)()
    yield s
    s.close()


def load(rel: str):
    return json.loads((FIX / rel).read_text())
