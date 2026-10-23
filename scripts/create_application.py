#!/usr/bin/env python3
"""Alias compatible de `scripts/cv.py new`.

Se mantiene para no romper atajos existentes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cv import main  # noqa: E402, I001

if __name__ == "__main__":
    raise SystemExit(main(["new", *sys.argv[1:]]))
