# Generated by Django 2.2.13 on 2020-08-14 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_user_staging_pk_to_bigint'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='email_status',
            field=models.CharField(max_length=126, null=True),
        ),
    ]
