from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _

from collections import namedtuple
from memoized import memoized

from corehq.apps.accounting.mixins import BillingModalsMixin
from corehq.apps.domain.decorators import (
    login_and_domain_required,
    login_required,
)
from corehq.apps.domain.models import Domain
from corehq.apps.domain.utils import normalize_domain_name
from corehq.apps.hqwebapp.views import BaseSectionPageView
from corehq.apps.users.models import Invitation
from corehq.util.quickcache import quickcache


def covid19(request):
    return select(request, next_view="app_exchange")

# Domain not required here - we could be selecting it for the first time. See notes domain.decorators
# about why we need this custom login_required decorator
@login_required
def select(request, do_not_redirect=False, next_view=None):
    if not hasattr(request, 'couch_user'):
        return redirect('registration_domain')

    # next_view must be a url that expects exactly one parameter, a domain name
    next_view = next_view or request.GET.get('next_view') or "domain_homepage"
    (domain_links, mirror_domain_links) = get_domain_dropdown_links(request.couch_user, view_name=next_view)
    if not domain_links:
        return redirect('registration_domain')

    email = request.couch_user.get_email()
    open_invitations = [e for e in Invitation.by_email(email) if not e.is_expired]

    additional_context = {
        'domain_links': domain_links,
        'mirror_domain_links': mirror_domain_links,
        'open_invitations': [] if next_view else open_invitations,
        'current_page': {'page_name': _('Select A Project')},
    }

    domain_select_template = "domain/select.html"
    last_visited_domain = request.session.get('last_visited_domain')
    if open_invitations \
       or do_not_redirect \
       or not last_visited_domain:
        return render(request, domain_select_template, additional_context)
    else:
        domain_obj = Domain.get_by_name(last_visited_domain)
        if domain_obj and domain_obj.is_active:
            # mirrors logic in login_and_domain_required
            if (
                request.couch_user.is_member_of(domain_obj, allow_mirroring=True)
                or (request.user.is_superuser and not domain_obj.restrict_superusers)
                or domain_obj.is_snapshot
            ):
                try:
                    return HttpResponseRedirect(reverse(next_view or 'dashboard_default',
                                                args=[last_visited_domain]))
                except Http404:
                    pass

        del request.session['last_visited_domain']
        return render(request, domain_select_template, additional_context)


Link = namedtuple('Link', ('name', 'url'))


@quickcache(['couch_user.username'])
def get_domain_dropdown_links(couch_user, view_name="domain_homepage"):
    from corehq.apps.users.models import DomainPermissionsMirrorSource
    domain_objects_by_name = {d.name: d for d in Domain.active_for_user(couch_user)}
    mirror_domain_objects_by_name = {}
    for domain_name in domain_objects_by_name:
        for mirror_domain in DomainPermissionsMirrorSource.mirror_domains(domain_name):
            if mirror_domain not in domain_objects_by_name:
                mirror_domain_objects_by_name[mirror_domain] = Domain.get_by_name(mirror_domain)

    def _domain_objects_to_links(objects):
        return sorted([Link(
            name=o.display_name(),
            url=reverse(view_name, args=[o.name]),
        ) for o in objects], key=lambda link: link.name.lower())

    return (
        _domain_objects_to_links(domain_objects_by_name.values()),
        _domain_objects_to_links(mirror_domain_objects_by_name.values()),
    )


class DomainViewMixin(object):
    """
        Paving the way for a world of entirely class-based views.
        Let's do this, guys. :-)

        Set strict_domain_fetching to True in subclasses to bypass the cache.
    """
    strict_domain_fetching = False

    @property
    @memoized
    def domain(self):
        domain = self.args[0] if len(self.args) > 0 else self.kwargs.get('domain', "")
        return normalize_domain_name(domain)

    @property
    @memoized
    def domain_object(self):
        domain_obj = Domain.get_by_name(self.domain, strict=self.strict_domain_fetching)
        if not domain_obj:
            raise Http404()
        return domain_obj


class LoginAndDomainMixin(object):

    @method_decorator(login_and_domain_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginAndDomainMixin, self).dispatch(*args, **kwargs)


class BaseDomainView(LoginAndDomainMixin, BillingModalsMixin, BaseSectionPageView, DomainViewMixin):

    @property
    def main_context(self):
        main_context = super(BaseDomainView, self).main_context
        main_context.update({
            'domain': self.domain,
        })
        return main_context

    @property
    @memoized
    def page_url(self):
        if self.urlname:
            return reverse(self.urlname, args=[self.domain])
