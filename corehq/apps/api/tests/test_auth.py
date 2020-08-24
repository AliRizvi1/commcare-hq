from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase, RequestFactory

from corehq.apps.api.resources.auth import LoginAuthentication, LoginAndDomainAuthentication, \
    RequirePermissionAuthentication
from corehq.apps.domain.models import Domain
from corehq.apps.users.models import WebUser, HQApiKey, Permissions, UserRole


class AuthenticationTestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.domain = 'api-test'
        cls.project = Domain.get_or_create_with_name(cls.domain, is_active=True)
        cls.username = 'alice@example.com'
        cls.password = '***'
        cls.user = WebUser.create(cls.domain, cls.username, cls.password, None, None)
        cls.api_key, _ = HQApiKey.objects.get_or_create(user=WebUser.get_django_user(cls.user))

    @classmethod
    def tearDownClass(cls):
        cls.project.delete()
        super().tearDownClass()

    def _get_request_with_api_key(self, domain=None):
        return self._get_request(domain,
                                 HTTP_AUTHORIZATION=self._contruct_api_auth_header(self.username, self.api_key))

    def _contruct_api_auth_header(self, username, api_key):
        return f'ApiKey {username}:{api_key.key}'

    def _get_request(self, domain=None, **extras):
        path = self._get_domain_path() if domain else ''
        request = self.factory.get(path, **extras)
        request.user = AnonymousUser()  # this is required for HQ's permission classes to resolve
        request.domain = domain  # as is this for any domain-specific request
        return request

    def _get_domain_path(self):
        return f'/a/{self.domain}/'

    def assertAuthenticationSuccess(self, auth_instance, request):
        # we can't use assertTrue, because auth failures can return "truthy" HttpResponse objects
        self.assertEqual(True, auth_instance.is_authenticated(request))

    def assertAuthenticationFail(self, auth_instance, request):
        result = auth_instance.is_authenticated(request)
        # currently auth classes return a 401/403 response in some scenarios
        # this should likely be changed to always return False
        # more discussion here: https://github.com/dimagi/commcare-hq/pull/28201#discussion_r461082885
        if isinstance(result, HttpResponse):
            self.assertIn(result.status_code, (401, 403))
        else:
            self.assertFalse(result)


class LoginAuthenticationTest(AuthenticationTestBase):

    def test_login_no_auth(self):
        self.assertAuthenticationFail(LoginAuthentication(), self._get_request())

    def test_login_with_auth(self):
        self.assertAuthenticationSuccess(LoginAuthentication(), self._get_request_with_api_key())


class LoginAndDomainAuthenticationTest(AuthenticationTestBase):

    def test_login_no_auth_no_domain(self):
        self.assertAuthenticationFail(LoginAndDomainAuthentication(), self._get_request())

    def test_login_no_auth_with_domain(self):
        self.assertAuthenticationFail(LoginAndDomainAuthentication(), self._get_request(domain=self.domain))

    def test_login_with_domain(self):
        self.assertAuthenticationSuccess(LoginAndDomainAuthentication(),
                                         self._get_request_with_api_key(domain=self.domain))

    def test_login_with_wrong_domain(self):
        project = Domain.get_or_create_with_name('api-test-fail', is_active=True)
        self.addCleanup(project.delete)
        self.assertAuthenticationFail(LoginAndDomainAuthentication(),
                                      self._get_request_with_api_key(domain=project.name))


class RequirePermissionAuthenticationTest(AuthenticationTestBase):
    require_edit_data = RequirePermissionAuthentication(Permissions.edit_data)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role_with_permission = UserRole.get_or_create_with_permissions(
            cls.domain, Permissions(edit_data=True), 'edit-data'
        )
        cls.role_without_permission = UserRole.get_or_create_with_permissions(
            cls.domain, Permissions(edit_data=False), 'no-edit-data'
        )
        cls.domain_admin = WebUser.create(cls.domain, 'domain_admin', '***', None, None, is_admin=True)
        cls.user_with_permission = WebUser.create(cls.domain, 'permission', '***', None, None,
                                                  role_id=cls.role_with_permission.get_id)
        cls.user_without_permission = WebUser.create(cls.domain, 'no-permission', '***', None, None,
                                                     role_id=cls.role_without_permission.get_id)

    def test_login_no_auth_no_domain(self):
        self.assertAuthenticationFail(self.require_edit_data, self._get_request())

    def test_login_no_auth_with_domain(self):
        self.assertAuthenticationFail(self.require_edit_data, self._get_request(domain=self.domain))

    def test_login_with_wrong_domain(self):
        project = Domain.get_or_create_with_name('api-test-fail', is_active=True)
        self.addCleanup(project.delete)
        self.assertAuthenticationFail(self.require_edit_data,
                                      self._get_request_with_api_key(domain=project.name))

    def test_login_with_domain_no_permissions(self):
        self.assertAuthenticationFail(self.require_edit_data,
                                      self._get_request_with_api_key(domain=self.domain))

    def test_login_with_domain_admin_default(self):
        api_key_with_default_permissions, _ = HQApiKey.objects.get_or_create(
            user=WebUser.get_django_user(self.domain_admin),
            name='default',
        )
        self.assertAuthenticationSuccess(self.require_edit_data,
                                         self._get_request(
                                             domain=self.domain,
                                             HTTP_AUTHORIZATION=self._contruct_api_auth_header(
                                                 self.domain_admin.username,
                                                 api_key_with_default_permissions
                                             )
                                         ))

    def test_domain_admin_with_explicit_roles(self):
        api_key_with_explicit_permissions, _ = HQApiKey.objects.get_or_create(
            user=WebUser.get_django_user(self.domain_admin),
            name='explicit_with_permission',
            role_id=self.role_with_permission.get_id,
        )
        api_key_without_explicit_permissions, _ = HQApiKey.objects.get_or_create(
            user=WebUser.get_django_user(self.domain_admin),
            name='explicit_without_permission',
            role_id=self.role_without_permission.get_id,
        )
        self.assertAuthenticationSuccess(self.require_edit_data,
                                         self._get_request(
                                             domain=self.domain,
                                             HTTP_AUTHORIZATION=self._contruct_api_auth_header(
                                                 self.domain_admin.username,
                                                 api_key_with_explicit_permissions
                                             )
                                         ))
        self.assertAuthenticationFail(self.require_edit_data,
                                      self._get_request(
                                          domain=self.domain,
                                          HTTP_AUTHORIZATION=self._contruct_api_auth_header(
                                              self.domain_admin.username,
                                              api_key_without_explicit_permissions
                                          )
                                      ))

    def test_login_with_explicit_permission(self):
        api_key_with_permissions, _ = HQApiKey.objects.get_or_create(
            user=WebUser.get_django_user(self.user_with_permission)
        )
        self.assertAuthenticationSuccess(self.require_edit_data,
                                         self._get_request(
                                             domain=self.domain,
                                             HTTP_AUTHORIZATION=self._contruct_api_auth_header(
                                                 self.user_with_permission.username,
                                                 api_key_with_permissions
                                             )
                                         ))

    def test_login_with_wrong_permission(self):
        api_key_without_permissions, _ = HQApiKey.objects.get_or_create(
            user=WebUser.get_django_user(self.user_without_permission)
        )
        self.assertAuthenticationFail(self.require_edit_data,
                                      self._get_request(
                                          domain=self.domain,
                                          HTTP_AUTHORIZATION=self._contruct_api_auth_header(
                                              self.user_without_permission.username,
                                              api_key_without_permissions
                                          )
                                      ))
