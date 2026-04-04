from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
TMP_KITTYCREW_ROOT = Path("/tmp/KittyCrew")

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture(autouse=True)
def cleanup_tmp_kittycrew_dirs():
    TMP_KITTYCREW_ROOT.mkdir(parents=True, exist_ok=True)
    existing_entries = {path.name for path in TMP_KITTYCREW_ROOT.iterdir()}
    yield
    if not TMP_KITTYCREW_ROOT.exists():
        return

    for path in TMP_KITTYCREW_ROOT.iterdir():
        if path.name in existing_entries:
            continue
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
