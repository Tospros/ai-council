#!/usr/bin/env python
"""
Main entry point for LLM Red Team application.
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / 'frontend'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')


def init_database():
    """Initialize the database."""
    from database import init_db
    print("Initializing database...")
    init_db()
    print("Database initialized!")


def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    print("Running migrations...")
    subprocess.run([
        sys.executable, '-m', 'alembic', 'upgrade', 'head'
    ], cwd=PROJECT_DIR)
    print("Migrations complete!")


def run_server(host='0.0.0.0', port=8000):
    """Run the Django development server."""
    import django
    from django.conf import settings
    from django.core.management import call_command

    # Setup Django
    os.chdir(PROJECT_DIR / 'frontend')
    django.setup()

    # Run server without autoreload (--noreload) to avoid Docker issues
    print(f"Starting server on {host}:{port}...")
    call_command('runserver', f'{host}:{port}', '--noreload')


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='LLM Red Team Application')
    parser.add_argument(
        'command',
        choices=['init', 'migrate', 'run', 'shell'],
        help='Command to run'
    )
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8000, help='Server port')

    args = parser.parse_args()

    if args.command == 'init':
        init_database()
    elif args.command == 'migrate':
        run_migrations()
    elif args.command == 'run':
        init_database()  # Ensure DB exists
        run_server(args.host, args.port)
    elif args.command == 'shell':
        os.chdir(PROJECT_DIR / 'frontend')
        import django
        django.setup()
        from django.core.management import call_command
        call_command('shell')


if __name__ == '__main__':
    main()
