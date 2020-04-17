from datetime import date
from django.core.management.base import BaseCommand
from corehq.apps.userreports.util import get_table_name
from corehq.apps.userreports.models import AsyncIndicator
from django.db import connections
from custom.icds_reports.models.aggregate import AwcLocation
from psycopg2.extensions import AsIs
from dimagi.utils.chunked import chunked


class Command(BaseCommand):
    help = "Rebuild Bihar delivery forms"
    BIHAR_STATE_ID = 'f9b47ea2ee2d8a02acddeeb491d3e175'

    def add_arguments(self, parser):
        parser.add_argument('--start_supervisor_id', required=False, dest='start_supervisor_id',
                            help='supervisor from where records are to fetch', default='')

    def get_supervisor_ids(self, start_supervisor_id):
        return AwcLocation.objects.filter(
            state_id=self.BIHAR_STATE_ID, aggregation_level=4, supervisor_id__gte=start_supervisor_id
        ).order_by('supervisor_id').values_list('supervisor_id', flat=True)

    def handle(self, *args, **kwargs):
        table_name = get_table_name('icds-cas', 'static-child_delivery_forms')
        # sort by supervisor_id and doc_id to improve the performance, sorting is needed to resume the queueing
        # if it fails in between.

        start_supervisor_id = kwargs.get('start_supervisor_id')
        bihar_state_id = 'f9b47ea2ee2d8a02acddeeb491d3e175'

        bihar_supervisor_ids = self.get_supervisor_ids(start_supervisor_id)
        count = 0
        chunk_size = 100
        for ids_chunk in chunked(bihar_supervisor_ids, chunk_size):
            query = """
                select doc_id from "%(table_name)s"
                where state_id=%(bihar_state_id)s AND supervisor_id in %(sup_ids)s
                order by doc_id
            """.format(table_name)

            query_params = {
                'table_name': AsIs(table_name),
                'bihar_state_id': bihar_state_id,
                'sup_ids': tuple(ids_chunk)
            }

            with connections['icds-ucr-citus'].cursor() as cursor:
                cursor.execute(query, query_params)
                doc_ids = cursor.fetchall()
                AsyncIndicator.objects.bulk_create([
                    AsyncIndicator(doc_id=doc_id,
                                   doc_type='XFormInstance',
                                   domain='icds-cas',
                                   indicator_config_ids=['static-icds-cas-static-child_delivery_forms'],
                                   date_created=date(2019, 1, 1)  # To prioritise in the queue
                                   )
                    for doc_id in doc_ids
                ])
            count += chunk_size
            print("Success till doc_id: {}".format(list(ids_chunk)[-1]))
            print("progress: {}/{}".format(count, len(bihar_supervisor_ids)))
