from pathlib import Path

# tools/helpers/paths.py -> tools/helpers -> tools
TOOLS_DIR = str(Path(__file__).resolve().parent.parent)
REPO_ROOT = str(Path(TOOLS_DIR).parent)
EXCEL_PATH = str(Path(TOOLS_DIR) / "data" / "vehicle_report.xlsx")
