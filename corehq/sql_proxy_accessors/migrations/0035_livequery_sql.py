# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-03 21:23

from django.conf import settings
from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration


migrator = RawSQLMigration(('corehq', 'sql_proxy_accessors', 'sql_templates'), {
    'PL_PROXY_CLUSTER_NAME': settings.PL_PROXY_CLUSTER_NAME
})


class Migration(migrations.Migration):

    dependencies = [
        ('sql_proxy_accessors', '0034_livequery_sql'),
    ]

    operations = [
        migrator.get_migration('get_modified_case_ids.sql'),
        migrator.get_migration('get_closed_and_deleted_ids.sql'),
        migrations.RunSQL(
            'DROP FUNCTION IF EXISTS filter_open_case_ids(TEXT, TEXT[])',
            'SELECT 1'
        ),
    ]
