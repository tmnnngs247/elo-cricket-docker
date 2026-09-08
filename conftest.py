"""
Makes `src` and `scripts` importable as top-level packages from the tests,
without needing __init__.py files (PEP 420 namespace packages) or an
installed package.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
