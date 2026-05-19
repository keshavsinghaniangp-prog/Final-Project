import sys
from pathlib import Path


def ensure_project_root() -> None:
    root = Path(__file__).parent.absolute()
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
