# coding: utf-8
from __future__ import unicode_literals, absolute_import

import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from fias.config import TABLES
from fias.models import Status, Version
from fias.importer.version import fetch_version_info


class Command(BaseCommand):
    help = 'Fill or update FIAS database'
    usage_str = 'Usage: ./manage.py fiasinfo --db-version [--update-version-info <yes|no>]'

    option_list = BaseCommand.option_list + (
        make_option('--db-version', action='store_true', dest='version', default=False,
                    help='Show version info'),

        make_option('--update-version-info', action='store', dest='update-version-info',
                    type='choice', choices=['yes', 'no'], default='yes',
                    help='Update list of available database versions from http://fias.nalog.ru'),


    )

    def handle(self, *args, **options):
        ver = options.pop('version')

        fetch = options.pop('update-version-info')
        if fetch == 'yes':
            fetch_version_info(update_all=True)

        if ver:
            latest_version = Version.objects.all().latest('dumpdate')
            print ('Latest version: {0}'.format(latest_version))
            statuses = dict((s.table, s) for s in Status.objects.select_related('ver').all())
            for table in TABLES:
                ver = statuses[table].ver.ver if table in statuses else 0
                print ('Table: {0}, version: {1}, actual: {2}'.format(
                    table,
                    ver if ver else 'unknown',
                    'No' if ver < latest_version.ver else 'Yes'
                ))

    def error(self, message, code=1):
        print(message)
        sys.exit(code)
