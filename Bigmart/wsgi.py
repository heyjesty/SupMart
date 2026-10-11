"""
WSGI config for Bigmart project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import logging
import os
import sqlite3

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Bigmart.settings')

application = get_wsgi_application()

log = logging.getLogger(__name__)

# Tables copied from the bundled db.sqlite3 into Postgres the first time the site
# starts on an empty database (parents before children).
SEED_MODELS = [
    'auth.User',
    'backend.categorydb',
    'backend.productdb',
    'homeapp.regdb',
    'homeapp.Checkout',
    'homeapp.OrderItem',
]


def _seed_from_sqlite():
    from django.apps import apps
    from django.conf import settings
    from django.core.management.color import no_style
    from django.db import connection, transaction

    seed_file = settings.BASE_DIR / 'db.sqlite3'
    if not seed_file.exists():
        return
    src = sqlite3.connect(f'file:{seed_file}?mode=ro', uri=True)
    src.row_factory = sqlite3.Row
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(424242)')
        Product = apps.get_model('backend', 'productdb')
        if Product.objects.exists():
            return  # already seeded
        used = []
        for label in SEED_MODELS:
            model = apps.get_model(label)
            fields = {f.column: f for f in model._meta.concrete_fields}
            objs = []
            for row in src.execute(f'SELECT * FROM "{model._meta.db_table}"'):
                data = {}
                for col in row.keys():
                    f = fields.get(col)
                    if f is not None:
                        val = row[col]
                        data[f.attname] = val if f.is_relation else f.to_python(val)
                objs.append(model(**data))
            model.objects.bulk_create(objs)
            used.append(model)
        with connection.cursor() as cur:
            for sql in connection.ops.sequence_reset_sql(no_style(), used):
                cur.execute(sql)
    src.close()
    log.warning('SupMart: seeded database from bundled db.sqlite3')


def _prepare_database():
    """Vercel has no build step for migrations, so apply them on cold start."""
    from django.core.management import call_command
    from django.db import connection

    if connection.vendor != 'postgresql':
        return
    try:
        call_command('migrate', interactive=False, verbosity=0)
        _seed_from_sqlite()
    except Exception:
        log.exception('SupMart: database preparation failed')


if os.environ.get('VERCEL'):
    _prepare_database()

# Vercel looks for a module-level "app"
app = application
