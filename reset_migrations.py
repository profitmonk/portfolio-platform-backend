#!/usr/bin/env python
"""
Reset Alembic migration state
"""
import os
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

load_dotenv()

def reset_migrations():
    """Reset migration state and apply current migrations"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found")
            return False
        
        print("🔧 Resetting Alembic migration state...")
        
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        # Get the latest migration file
        import glob
        migration_files = glob.glob("alembic/versions/*.py")
        if not migration_files:
            print("❌ No migration files found")
            return False
        
        # Get the latest migration revision
        latest_file = max(migration_files)
        # Extract revision from filename (first part before underscore)
        revision = os.path.basename(latest_file).split('_')[0]
        
        print(f"📝 Stamping database with revision: {revision}")
        
        # Stamp the database with current revision
        command.stamp(alembic_cfg, revision)
        
        print("✅ Migration state reset successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

if __name__ == "__main__":
    reset_migrations()
