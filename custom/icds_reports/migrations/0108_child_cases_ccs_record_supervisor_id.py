# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-03-12 10:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0107_citus_composite_key'),
    ]

    operations = [
        migrations.RunSQL("ALTER TABLE ccs_record_monthly ADD COLUMN supervisor_id text"),
        migrations.RunSQL("ALTER TABLE child_health_monthly ADD COLUMN supervisor_id text")
    ]
