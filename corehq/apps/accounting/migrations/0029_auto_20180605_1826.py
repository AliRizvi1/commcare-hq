# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-05 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0028_auto_20180604_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='softwareplan',
            name='is_customer_software_plan',
            field=models.BooleanField(default=False),
        ),
    ]
