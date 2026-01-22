# Generated migration for enabling pgvector extension

from django.db import migrations


def enable_pgvector_extension(apps, schema_editor):
    """Enable pgvector extension only if using PostgreSQL."""
    # Check if using SQLite (skip extension for SQLite)
    if schema_editor.connection.vendor == 'sqlite':
        return
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def disable_pgvector_extension(apps, schema_editor):
    """Disable pgvector extension only if using PostgreSQL."""
    # Check if using SQLite (skip extension for SQLite)
    if schema_editor.connection.vendor == 'sqlite':
        return
    schema_editor.execute("DROP EXTENSION IF EXISTS vector;")


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
