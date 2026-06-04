"""Backup automatico diario de la base de datos."""

import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path


def run_backup(db_path="gametronix.db", backup_dir="backups", keep_days=7):
    """Crea un backup de la BD si no se ha hecho hoy. Mantiene los ultimos N dias."""
    if not os.path.exists(db_path):
        return None

    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    today_backup = backup_path / f"gametronix_{today}.db"

    # Si ya hay backup de hoy, no duplicar
    if today_backup.exists():
        return str(today_backup)

    # Crear backup
    shutil.copy2(db_path, str(today_backup))

    # Limpiar backups viejos
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in backup_path.glob("gametronix_*.db"):
        try:
            date_str = f.stem.replace("gametronix_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                f.unlink()
        except Exception:
            pass

    return str(today_backup)
