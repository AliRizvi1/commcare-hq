# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-17 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0021_add_user_data_filter'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertschedule',
            name='stop_date_case_property_name',
            field=models.CharField(max_length=126, null=True),
        ),
        migrations.AddField(
            model_name='timedschedule',
            name='stop_date_case_property_name',
            field=models.CharField(max_length=126, null=True),
        ),
    ]
