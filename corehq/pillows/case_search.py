import inspect
import re

from casexml.apps.case.models import CommCareCase
from corehq.apps.case_search.exceptions import CaseSearchNotEnabledException
from corehq.apps.case_search.models import case_search_enabled_for_domain
from corehq.apps.change_feed import topics
from corehq.apps.change_feed.consumer.feed import KafkaChangeFeed
from corehq.elastic import get_es_new
from corehq.pillows.case import CASE_ES_TYPE, CasePillow
from corehq.pillows.const import CASE_SEARCH_ALIAS
from corehq.pillows.mappings.case_search_mapping import CASE_SEARCH_INDEX, \
    CASE_SEARCH_MAPPING
from corehq.util.couch_helpers import paginate_view
from pillowtop.checkpoints.manager import PillowCheckpoint, \
    PillowCheckpointEventHandler
from pillowtop.es_utils import ElasticsearchIndexMeta
from pillowtop.feed.couch import change_from_couch_row
from pillowtop.feed.interface import Change
from pillowtop.pillow.interface import ConstructedPillow
from pillowtop.processors.elastic import ElasticProcessor
from pillowtop.reindexer.change_providers.couch import CouchViewChangeProvider
from pillowtop.reindexer.reindexer import PillowReindexer


class CaseSearchPillow(CasePillow):
    # TODO: Remove this once elasticsearch gets bootstrapped with new pillows
    # (Used in order to set up index)
    """
    Nested case properties indexer.
    """
    es_alias = CASE_SEARCH_ALIAS

    es_index = CASE_SEARCH_INDEX
    default_mapping = CASE_SEARCH_MAPPING

    def change_trigger(self, changes_dict):
        return


def transform_case_for_elasticsearch(doc_dict):
    doc = {
        desired_property: doc_dict.get(desired_property)
        for desired_property in CASE_SEARCH_MAPPING['properties'].keys()
        if desired_property != 'case_properties'
    }
    doc['_id'] = doc_dict.get('_id')
    doc['case_properties'] = _get_case_properties(doc_dict)
    return doc


def _get_case_properties(doc_dict):
    base_case_properties = [
        {'key': 'name', 'value': doc_dict.get('name')},
        {'key': 'external_id', 'value': doc_dict.get('external_id')}
    ]
    dynamic_case_properties = [
        {'key': key, 'value': value}
        for key, value in doc_dict.iteritems()
        if _is_dynamic_case_property(key)
    ]

    return base_case_properties + dynamic_case_properties


def _is_dynamic_case_property(prop):
    """
    Finds whether {prop} is a dynamic property of CommCareCase. If so, it is likely a case property.
    """
    return not inspect.isdatadescriptor(getattr(CommCareCase, prop, None)) and re.search(r'^[a-zA-Z]', prop)


class CaseSearchPillowProcessor(ElasticProcessor):
    def process_change(self, pillow_instance, change, do_set_checkpoint):
        domain = self._get_domain(change)
        change_object = self._get_change_object(change)
        if domain and case_search_enabled_for_domain(domain):
            super(CaseSearchPillowProcessor, self).process_change(
                pillow_instance, change_object, do_set_checkpoint
            )

    def _get_domain(self, change):
        if isinstance(change, dict):
            return change.get('key', [])[0]
        elif isinstance(change, Change):
            return change.metadata.domain

    def _get_change_object(self, change):
        if isinstance(change, dict):
            return change_from_couch_row(change)
        elif isinstance(change, Change):
            return change


def get_case_search_to_elasticsearch_pillow(pillow_id='CaseSearchToElasticsearchPillow'):
    checkpoint = PillowCheckpoint(
        'case-search-to-elasticsearch',
    )
    case_processor = CaseSearchPillowProcessor(
        elasticsearch=get_es_new(),
        index_meta=ElasticsearchIndexMeta(index=CASE_SEARCH_INDEX, type=CASE_ES_TYPE),
        doc_prep_fn=transform_case_for_elasticsearch
    )
    return ConstructedPillow(
        name=pillow_id,
        document_store=None,
        checkpoint=checkpoint,
        change_feed=KafkaChangeFeed(topics=[topics.CASE], group_id='cases-to-es'),
        processor=case_processor,
        change_processed_event_handler=PillowCheckpointEventHandler(
            checkpoint=checkpoint, checkpoint_frequency=100,
        ),
    )


def get_couch_case_search_reindexer(domain=None):
    # TODO: Figure out how to not fetch every single case from the DB when running a full reindex

    # TODO: Remove this
    # It initializes the es index if it doesn't exist
    CaseSearchPillow()

    view_kwargs = {'include_docs': True}

    if domain is not None:
        if not case_search_enabled_for_domain(domain):
            raise CaseSearchNotEnabledException("{} does not have case search enabled".format(domain))

        startkey = [domain]
        endkey = [domain, {}, {}]
        view_kwargs.update({'startkey': startkey, 'endkey': endkey})

    return PillowReindexer(get_case_search_to_elasticsearch_pillow(), CouchViewChangeProvider(
        document_class=CommCareCase,
        view_name='cases_by_owner/view',
        view_kwargs=view_kwargs,
    ))


def delete_case_search_cases(domain):
    if domain is None or isinstance(domain, dict):
        raise TypeError("Domain attribute is required")

    startkey = [domain]
    endkey = [domain, {}, {}]
    es = get_es_new()
    db = CommCareCase.get_db()

    for item in paginate_view(db, 'cases_by_owner/view', 100, startkey=startkey, endkey=endkey, reduce=False):
        if es.exists(CASE_SEARCH_INDEX, CASE_ES_TYPE, item['id']):
            es.delete(CASE_SEARCH_INDEX, CASE_ES_TYPE, item['id'])
