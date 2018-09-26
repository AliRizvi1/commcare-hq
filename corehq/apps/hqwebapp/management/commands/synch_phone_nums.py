from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from django.core.management.base import BaseCommand

from corehq.apps.users.models import CommCareUser
from corehq.apps.sms.tasks import sync_user_phone_numbers as sms_sync_user_phone_numbers
from corehq.form_processor.backends.sql.dbaccessors import CaseReindexAccessor, iter_all_rows
from corehq.messaging.tasks import sync_case_for_messaging
from corehq.util.log import with_progress_bar
from corehq.sql_db.util import get_db_aliases_for_partitioned_query
from corehq.form_processor.utils import should_use_sql_backend
from corehq.apps.couch_sql_migration.couchsqlmigration import _get_case_iterator


class Command(BaseCommand):
    help = "Resync all contacts' phone numbers for given projects"

    def add_arguments(self, parser):
        parser.add_argument('-d', '--domains', type=str, help='Comma separated domain list')

    def handle(self, **kwargs):
        domains = kwargs['domains'].split(',')

        for domain in domains:
            print("Resync all contacts' phone numbers for project %s  " % domain)
            print("Synching for phone numbers")
            commcare_user_ids = (
                CommCareUser.ids_by_domain(domain, is_active=True) +
                CommCareUser.ids_by_domain(domain, is_active=False)
            )
            for user_id in with_progress_bar(commcare_user_ids):
                sms_sync_user_phone_numbers.delay(user_id)

            self.sync_cases(domain)

    def sync_cases(self, domain):
        db_aliases = get_db_aliases_for_partitioned_query()
        db_aliases.sort()
        if should_use_sql_backend(domain):
            case_accessor = CaseReindexAccessor(domain)
            for case in iter_all_rows(case_accessor):
                sync_case_for_messaging.delay(domain, case.case_id)
        else:
            changes = _get_case_iterator(self.domain).iter_all_changes()
            for case in changes:
                sync_case_for_messaging.delay(domain, case.id)
