# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-31 19:21

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0034_remove_subscription_date_delay_invoicing'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingaccount',
            name='restrict_domain_creation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='billingaccount',
            name='enterprise_restricted_signup_domains',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=128), blank=True, default=list, size=None),
        ),
        migrations.AlterField(
            model_name='subscriptionadjustment',
            name='method',
            field=models.CharField(choices=[('USER', 'User'), ('INTERNAL', 'Ops'), ('TASK', '[Deprecated] Task (Invoicing)'), ('TRIAL', '30 Day Trial'), ('AUTOMATIC_DOWNGRADE', 'Automatic Downgrade'), ('DEFAULT_COMMUNITY', 'Default to Community'), ('INVOICING', 'Invoicing')], default='INTERNAL', max_length=50),
        ),
        migrations.AddField(
            model_name='billingaccount',
            name='restrict_signup',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='billingaccount',
            name='restrict_signup_email',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='billingaccount',
            name='restrict_signup_message',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='billingaccount',
            name='is_customer_billing_account',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
