#!/usr/bin/env python3
"""Compatibility wrapper for the packaged Fable Harness installer."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fable_harness.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
