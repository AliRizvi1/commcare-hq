import base64

from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from corehq.apps.domain.utils import clear_domain_names
from tastypie.models import ApiKey

from corehq.apps.accounting.models import (
    BillingAccount,
    DefaultProductPlan,
    SoftwarePlanEdition,
    Subscription,
    SubscriptionAdjustment,
)
from corehq.apps.domain.models import Domain
from corehq.apps.export.const import PROPERTY_TAG_CASE
from corehq.apps.export.models import (
    FormExportDataSchema,
    ExportGroupSchema,
    MAIN_TABLE,
    PathNode,
    ExportItem,
    CaseExportDataSchema,
    ScalarItem,
    FormExportInstance,
    CaseExportInstance,
)
from corehq.apps.users.models import WebUser
from corehq.pillows.mappings.case_mapping import CASE_INDEX_INFO
from corehq.pillows.mappings.xform_mapping import XFORM_INDEX_INFO
from corehq.util.elastic import ensure_index_deleted, reset_es_index


class OdataTestMixin(object):

    view_urlname = None

    @classmethod
    def _set_up_class(cls):
        cls.client = Client()
        clear_domain_names('test_domain')
        cls.domain = Domain(name='test_domain')
        cls.domain.save()
        cls.web_user = WebUser.create(cls.domain.name, 'test_user', 'my_password')
        cls._setup_user_permissions()
        cls.app_id = '1234'
        cls.instance = cls.get_instance(cls.domain.name)
        cls.instance.is_odata_config = True
        cls.instance.transform_dates = False
        cls.instance.save()

    @classmethod
    def get_instance(cls, domain_name):
        raise NotImplementedError()

    @classmethod
    def _teardownclass(cls):
        cls.domain.delete()

    @classmethod
    def _setup_accounting(cls):
        call_command('cchq_prbac_bootstrap')
        cls.account, _ = BillingAccount.get_or_create_account_by_domain(cls.domain.name, created_by='')
        plan_version = DefaultProductPlan.get_default_plan_version(SoftwarePlanEdition.ADVANCED)
        cls.subscription = Subscription.new_domain_subscription(cls.account, cls.domain.name, plan_version)

    @classmethod
    def _teardown_accounting(cls):
        SubscriptionAdjustment.objects.all().delete()
        cls.subscription.delete()
        cls.account.delete()

    @classmethod
    def _setup_user_permissions(cls):
        cls.web_user.set_role(cls.domain.name, 'admin')
        cls.web_user.save()

    def _execute_query(self, credentials):
        return self.client.get(self.view_url, HTTP_AUTHORIZATION='Basic ' + credentials)

    @classmethod
    def _get_correct_credentials(cls):
        return OdataTestMixin._get_basic_credentials(cls.web_user.username, 'my_password')

    @staticmethod
    def _get_basic_credentials(username, password):
        return base64.b64encode("{}:{}".format(username, password).encode('utf-8')).decode('utf-8')

    @property
    def view_url(self):
        return reverse(self.view_urlname, kwargs={'domain': self.domain.name, 'config_id': self.instance._id})


class CaseOdataTestMixin(OdataTestMixin):

    @classmethod
    def get_instance(cls, domain_name):
        return CaseExportInstance.generate_instance_from_schema(
            CaseExportDataSchema(
                domain=domain_name,
                group_schemas=[
                    ExportGroupSchema(
                        path=MAIN_TABLE,
                        items=[
                            ScalarItem(
                                path=[PathNode(name='p1')],
                                label='p1',
                                last_occurrences={},
                            ),
                        ],
                        last_occurrences={cls.app_id: 3},
                    ),
                ],
            ))


class FormOdataTestMixin(OdataTestMixin):

    @classmethod
    def get_instance(cls, domain_name):
        return FormExportInstance.generate_instance_from_schema(
            FormExportDataSchema(
                domain=domain_name,
                group_schemas=[
                    ExportGroupSchema(
                        path=MAIN_TABLE,
                        items=[
                            ExportItem(
                                path=[PathNode(name='data'), PathNode(name='question1')],
                                label='Question 1',
                                last_occurrences={
                                    cls.app_id: 3,
                                },
                            ),
                            ExportItem(
                                path=[PathNode(name='data'), PathNode(name='@case_id')],
                                label='@case_id',
                                tag=PROPERTY_TAG_CASE,
                                last_occurrences={
                                    cls.app_id: 3,
                                },
                            )
                        ],
                        last_occurrences={
                            cls.app_id: 3,
                        },
                    ),
                ],
            ))


def generate_api_key_from_web_user(web_user):
    api_key = ApiKey.objects.get_or_create(user=web_user.get_django_user())[0]
    api_key.key = api_key.generate_key()
    api_key.save()
    return api_key


def setup_es_case_index():
    reset_es_index(CASE_INDEX_INFO)


def setup_es_form_index():
    reset_es_index(XFORM_INDEX_INFO)


def ensure_es_case_index_deleted():
    ensure_index_deleted(CASE_INDEX_INFO.index)


def ensure_es_form_index_deleted():
    ensure_index_deleted(XFORM_INDEX_INFO.index)
