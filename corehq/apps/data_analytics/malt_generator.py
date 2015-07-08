from corehq.apps.app_manager.models import Application
from corehq.apps.data_analytics.models import MALTRow
from corehq.apps.domain.models import Domain
from corehq.apps.smsforms.app import COMMCONNECT_DEVICE_ID
from corehq.apps.sofabed.models import FormData
from corehq.util.quickcache import quickcache


class MALTTableGenerator(object):
    """
        Populates SQL table with data for given datespan
        See .models.MALTRow
    """

    def __init__(self, datespan_object):
        self.datespan = datespan_object

    def build_table(self):

        for domain in Domain.get_all():
            malt_rows_to_save = []
            for user in domain.all_users():
                forms_query = self.get_forms_queryset(user._id, domain.name)
                num_of_forms = forms_query.count()
                apps_submitted_for = [app_id for (app_id,) in
                                      forms_query.values_list('app_id').distinct()]

                for app_id in apps_submitted_for:
                    wam, pam = self._wam_pams(domain.name, app_id)
                    db_row = MALTRow(
                        month=self.datespan.startdate,
                        user_id=user._id,
                        username=user.username,
                        email=user.email,
                        is_web_user=user.doc_type == 'WebUser',
                        domain_name=domain.name,
                        num_of_forms=num_of_forms,
                        app_id=app_id,
                        wam=wam,
                        pam=pam
                    )
                    malt_rows_to_save.append(db_row)
            MALTRow.objects.bulk_create(malt_rows_to_save)

    def get_forms_queryset(self, user_id, domain_name):
        start_date = self.datespan.startdate
        end_date = self.datespan.enddate

        return FormData.objects.exclude(device_id=COMMCONNECT_DEVICE_ID).filter(
            user_id=user_id,
            domain=domain_name,
            received_on__range=(start_date, end_date)
        )

    @classmethod
    @quickcache(['domain', 'app_id'])
    def _wam_pams(cls, domain, app_id):

        app = Application.get(app_id)
        wam, pam = (getattr(app, 'amplifies_workers', 'not_set'),
                    getattr(app, 'amplifies_project', 'not_set'))
        return wam, pam
