import textwrap

from celery.task import task
from collections import defaultdict

from django.conf import settings
from django.utils.translation import ugettext as _

from dimagi.utils.logging import notify_exception

from corehq import toggles
from corehq.apps.app_manager.dbaccessors import get_apps_in_domain
from corehq.apps.app_manager.util import is_linked_app
from corehq.apps.app_manager.views.utils import update_linked_app
from corehq.apps.hqwebapp.tasks import send_mail_async
from corehq.apps.linked_domain.const import MODEL_APP, MODEL_CASE_SEARCH, MODEL_REPORT
from corehq.apps.linked_domain.dbaccessors import get_linked_domains
from corehq.apps.linked_domain.ucr import update_linked_ucr
from corehq.apps.linked_domain.updates import update_model_type
from corehq.apps.linked_domain.util import pull_missing_multimedia_for_app_and_notify
from corehq.apps.userreports.dbaccessors import get_report_configs_for_domain
from corehq.apps.users.models import CouchUser


@task(queue='background_queue')
def pull_missing_multimedia_for_app_and_notify_task(domain, app_id, email=None):
    pull_missing_multimedia_for_app_and_notify(domain, app_id, email)


@task(queue='background_queue')
def push_models(master_domain, models, linked_domains, build_apps, username):
    user = CouchUser.get_by_username(username)
    manager = ReleaseManager(master_domain, user)
    manager.release(models, linked_domains, build_apps)
    manager.send_email()


def _handle_app(domain_link, model, user, build_and_release=False):
    if toggles.MULTI_MASTER_LINKED_DOMAINS.enabled(domain_link.linked_domain):
        return _("Multi master flag is in use")

    app_id = model['detail']['app_id']
    found = False
    error_prefix = ""
    try:
        for linked_app in get_apps_in_domain(domain_link.linked_domain, include_remote=False):
            if is_linked_app(linked_app) and linked_app.family_id == app_id:
                found = True
                app = update_linked_app(linked_app, app_id, user.user_id)

        if not found:
            return _("Could not find app")

        if build_and_release:
            error_prefix = _("Updated app but did not build or release: ")
            build = app.make_build()
            build.is_released = True
            raise Exception("couldn't save!")
            build.save(increment_version=False)
    except Exception as e:  # intentionally broad
        return error_prefix + str(e)


def _handle_report(domain_link, model):
    report_id = model['detail']['report_id']
    found = False
    for linked_report in get_report_configs_for_domain(domain_link.linked_domain):
        if linked_report.report_meta.master_id == report_id:
            found = True
            update_linked_ucr(domain_link, linked_report.get_id)

    if not found:
        return _("Could not find report")


def _handle_case_search(domain_link, model, user):
    if not toggles.SYNC_SEARCH_CASE_CLAIM.enabled(domain_link.linked_domain):
        return _("Case claim flag is not on")

    return _handle_model(domain_link, model, user)


def _handle_model(domain_link, model, user):
    update_model_type(domain_link, model['type'], model_detail=model['detail'])
    domain_link.update_last_pull(model['type'], user._id)


class ReleaseManager():
    def __init__(self, master_domain, user):
        self.master_domain = master_domain
        self.user = user
        self.linked_domains = []
        self.models = []
        self.errors_by_domain = defaultdict(list)
        self.successes_by_domain = defaultdict(list)

    def release(self, models, linked_domains, build_apps):
        self.linked_domains = linked_domains
        self.models = models
        domain_links_by_linked_domain = {link.linked_domain: link for link in get_linked_domains(self.master_domain)}
        for linked_domain in self.linked_domains:
            if linked_domain not in domain_links_by_linked_domain:
                self.errors_by_domain[linked_domain].append(_("Project space {} is no longer linked to {}. No content "
                                                              "was released to it.").format(self.master_domain, linked_domain))
                continue
            domain_link = domain_links_by_linked_domain[linked_domain]
            for model in self.models:
                error = None
                try:
                    if model['type'] == MODEL_APP:
                        error = _handle_app(domain_link, model, self.user, build_apps)
                    elif model['type'] == MODEL_REPORT:
                        error = _handle_report(domain_link, model)
                    elif model['type'] == MODEL_CASE_SEARCH:
                        error = _handle_case_search(domain_link, model, self.user)
                    else:
                        error = _handle_model(domain_link, model, self.user)
                except Exception as e:   # intentionally broad
                    error = str(e)
                    notify_exception(None, "Exception pushing linked domains: {}".format(e))

                if error:
                    self.errors_by_domain[linked_domain].append(_("Could not update {}: {}").format(model['name'], error))
                else:
                    self.successes_by_domain[linked_domain].append(_("Updated {} successfully").format(model['name']))

    def send_email(self):
        subject = _("Linked project release complete.")
        if self.errors_by_domain:
            subject += _(" Errors occurred.")

        error_domain_count = len(self.errors_by_domain)
        success_domain_count = len(self.linked_domains) - error_domain_count
        message = _("""
Release complete. {} project(s) succeeded. {}

The following content was released:
{}

The following linked project spaces received content:
        """).format(
            success_domain_count,
            _("{} project(s) encountered errors.").format(error_domain_count) if error_domain_count else "",
            "\n".join(["- " + m['name'] for m in self.models])
        )
        for linked_domain in self.linked_domains:
            if linked_domain not in self.errors_by_domain:
                message += _("\n- {} updated successfully").format(linked_domain)
            else:
                message += _("\n- {} encountered errors:").format(linked_domain)
                for msg in self.errors_by_domain[linked_domain] + self.successes_by_domain[linked_domain]:
                    message += "\n   - " + msg
        send_mail_async.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email or self.user.username])
