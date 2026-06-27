"""Management command: создаёт резервную копию SQLite-БД.

Использование:
    python manage.py backup_db                    # backup_<timestamp>.sqlite3 в BACKUP_DIR
    python manage.py backup_db --keep 7           # хранить только 7 последних
    python manage.py backup_db --output /tmp/db   # в другую директорию

Для PostgreSQL рекомендуется pg_dump (не реализовано здесь, т.к. это dev-проект на SQLite).
"""
import shutil
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Создаёт резервную копию SQLite-БД (с ротацией)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep', type=int, default=0,
            help='Хранить только N последних бэкапов (0 = хранить все)',
        )
        parser.add_argument(
            '--output', type=str, default=None,
            help='Директория для бэкапов (default: BACKUP_DIR из settings или BACKUPS_DIR env)',
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default'].get('NAME', '')
        if not db_path:
            raise CommandError('DATABASES default NAME не настроен')

        db_file = Path(db_path)
        if not db_file.exists():
            raise CommandError(f'БД не найдена: {db_file}')

        # Определить директорию для бэкапов
        backup_dir = Path(
            options.get('output')
            or getattr(settings, 'BACKUP_DIR', None)
            or settings.BASE_DIR / 'backups'
        )
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Сформировать имя файла
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        backup_name = f"backup_{timestamp}_{db_file.name}"
        backup_path = backup_dir / backup_name

        # Копировать через .backup() для согласованности (если SQLite)
        # Для надёжности — просто shutil.copy2
        try:
            shutil.copy2(db_file, backup_path)
        except Exception as e:
            raise CommandError(f'Не удалось создать бэкап: {e}')

        size_mb = backup_path.stat().st_size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f'✓ Бэкап создан: {backup_path} ({size_mb:.2f} MB)'
        ))

        # Ротация: оставить N последних
        keep = options.get('keep', 0)
        if keep > 0:
            backups = sorted(
                backup_dir.glob(f'backup_*_{db_file.name}'),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old_backup in backups[keep:]:
                try:
                    old_backup.unlink()
                    self.stdout.write(f'  Удалён старый бэкап: {old_backup.name}')
                except OSError as e:
                    self.stdout.write(self.style.WARNING(
                        f'  Не удалось удалить {old_backup.name}: {e}'
                    ))

        # Показать список всех бэкапов
        all_backups = sorted(
            backup_dir.glob(f'backup_*_{db_file.name}'),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if all_backups:
            self.stdout.write(f'\nВсего бэкапов: {len(all_backups)}')
            for b in all_backups[:5]:
                age = time.time() - b.stat().st_mtime
                size = b.stat().st_size / (1024 * 1024)
                self.stdout.write(f'  {b.name}  {size:.2f} MB  ({int(age)}s ago)')

        self.stdout.write(self.style.SUCCESS('\nГотово.'))