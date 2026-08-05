from pathlib import Path

# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "database"

STORAGE_DIR = BASE_DIR / "storage"

ATTACHMENTS_DIR = STORAGE_DIR / "attachments"

QRCODES_DIR = STORAGE_DIR / "qrcodes"

# ==========================================================
# DATABASE
# ==========================================================

DATABASE_FILE = DATABASE_DIR / "lims.db"

# ==========================================================
# GOOGLE DRIVE
# ==========================================================

GOOGLE_CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = "LIMS"

APP_VERSION = "0.1"

LAB_NAME = "Laboratory of Molecular Biology"