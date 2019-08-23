# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-09-13 14:54
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling_partitioned', '0005_timed_schedule_instance_schedule_revision'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='alertscheduleinstance',
            unique_together=set([('alert_schedule_id', 'recipient_type', 'recipient_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='timedscheduleinstance',
            unique_together=set([('timed_schedule_id', 'recipient_type', 'recipient_id')]),
        ),
    ]
