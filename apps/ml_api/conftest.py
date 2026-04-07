import sys
from pathlib import Path

# Ensure both app and libs/common are importable when running from apps/ml_api/
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root / "libs" / "common" / "src"))
sys.path.insert(0, str(Path(__file__).parent))
