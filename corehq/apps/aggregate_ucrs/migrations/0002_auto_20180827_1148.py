# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-27 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aggregate_ucrs', '0001_initial_squashed_0008_auto_20180625_1105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='secondarycolumn',
            name='aggregation_type',
            field=models.CharField(choices=[('sum', 'Sum'), ('min', 'Min'), ('max', 'Max'), ('avg', 'Average'), ('count', 'Count'), ('count_unique', 'Count Unique Values'), ('nonzero_sum', 'Has a nonzero sum (1 if sum is nonzero else 0).')], max_length=20),
        ),
        migrations.AlterField(
            model_name='secondarytabledefinition',
            name='join_column_primary',
            field=models.CharField(max_length=63),
        ),
    ]
