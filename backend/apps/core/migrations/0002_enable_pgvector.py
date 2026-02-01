# Generated migration for enabling pgvector extension

from django.db import migrations
import logging

logger = logging.getLogger(__name__)


def enable_pgvector_extension(apps, schema_editor):
    """Enable pgvector extension only if using PostgreSQL."""
    # Check if using SQLite (skip extension for SQLite)
    if schema_editor.connection.vendor == 'sqlite':
        return
    try:
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("pgvector extension created successfully")
    except Exception as e:
        # If extension creation fails (e.g., insufficient privileges),
        # log a warning but don't fail the migration
        logger.warning(
            f"Could not create pgvector extension: {e}. "
            "Please ask your database administrator to run: "
            "CREATE EXTENSION IF NOT EXISTS vector;"
        )


def disable_pgvector_extension(apps, schema_editor):
    """Disable pgvector extension only if using PostgreSQL."""
    # Check if using SQLite (skip extension for SQLite)
    if schema_editor.connection.vendor == 'sqlite':
        return
    try:
        schema_editor.execute("DROP EXTENSION IF EXISTS vector;")
        logger.info("pgvector extension dropped successfully")
    except Exception as e:
        logger.warning(f"Could not drop pgvector extension: {e}")


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Enable pgvector extension (PostgreSQL only)
        migrations.RunPython(
            enable_pgvector_extension,
            disable_pgvector_extension,
        ),
    ]
