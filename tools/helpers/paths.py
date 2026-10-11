from pathlib import Path

# tools/helpers/paths.py -> tools/helpers -> tools
TOOLS_DIR = str(Path(__file__).resolve().parent.parent)
REPO_ROOT = str(Path(TOOLS_DIR).parent)
EXCEL_PATH = str(Path(TOOLS_DIR) / "data" / "vehicle_report.xlsx")


def match_disk_case(rel_path: str) -> str:
    """Return rel_path (relative to REPO_ROOT) with each folder name using the casing found on disk.

    Windows is case-insensitive, Linux is not, so paths from the Excel sheet must match the real folders.
    Components that don't exist yet are kept as given.
    """
    parts = rel_path.replace("\\", "/").split("/")
    current = Path(REPO_ROOT)
    resolved = []
    exists = True
    for part in parts:
        if exists:
            try:
                names = [entry.name for entry in current.iterdir()]
            except OSError:
                names = []
            if part in names:
                match = part
            else:
                match = next((n for n in names if n.lower() == part.lower()), None)
            if match is None:
                exists = False
            else:
                part = match
        resolved.append(part)
        current = current / part
    return "/".join(resolved)
