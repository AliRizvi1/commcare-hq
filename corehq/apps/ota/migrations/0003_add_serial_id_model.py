# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-09-29 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ota', '0002_alter_db_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='SerialIdBucket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('bucket_id', models.CharField(max_length=255)),
                ('current_value', models.IntegerField(default=-1)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='serialidbucket',
            unique_together=set([('domain', 'bucket_id')]),
        ),
        migrations.AlterIndexTogether(
            name='serialidbucket',
            index_together=set([('domain', 'bucket_id')]),
        ),
    ]
