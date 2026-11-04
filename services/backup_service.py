"""
Database Backup Service for Tewabu ERP.
Safely creates timestamped copies of the SQLite database.
"""

from datetime import datetime
from pathlib import Path
import shutil
from config.settings import settings

def create_database_backup() -> Path:
    """
    Create a timestamped backup of the current SQLite database.
    Returns path to backup file.
    """
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Extract source file path from sqlite+aiosqlite:///...
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        source_path_str = db_url.split(":///")[-1]
        source_path = Path(source_path_str).resolve()
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source database not found at {source_path}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"tewabu_erp_backup_{timestamp}.db"
        dest_path = settings.BACKUP_DIR / backup_filename
        
        shutil.copy2(source_path, dest_path)
        return dest_path
    else:
        raise ValueError("Backups currently supported for SQLite databases.")
