from collections import defaultdict

import logging

from django.core.management.base import BaseCommand

from corehq.dbaccessors.couchapps.all_docs import get_all_docs_with_doc_types, get_doc_count_by_type
from corehq.util.couchdb_management import couch_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Given a couch document type, iterates over all documents and reports back
        on whether those attributes are ever null and what their largest values are.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'doc_type',
        )
        parser.add_argument(
            '-s',
            '--db',
            dest='db',
            help='Slug for couch data base. Leave off if querying main commcarehq db.',
        )

    def handle(self, doc_type, **options):
        db = couch_config.get_db(options.get('db', None))
        key_counts = defaultdict(lambda: 0)
        max_lengths = defaultdict(lambda: 0)

        print("Found {} {} docs\n".format(get_doc_count_by_type(db, doc_type), doc_type))

        def _evaluate_doc(doc, prefix=None):
            for key, value in doc.items():
                if prefix:
                    key = f"{prefix}.{key}"
                if not value or isinstance(value, bool):
                    continue
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            _evaluate_doc(item, prefix=key)
                    length = len(value)
                else:
                    length = len(str(value))
                max_lengths[key] = max(length, max_lengths[key])
                key_counts[key] += 1

        docs = get_all_docs_with_doc_types(db, [doc_type])
        for doc in docs:
            _evaluate_doc(doc)

        max_count = max(key_counts.values())
        for key in sorted(key_counts):
            print("{} is {} blank and has max length of {}".format(
                key,
                'never' if key_counts[key] == max_count else 'sometimes',
                max_lengths[key]
            ))
