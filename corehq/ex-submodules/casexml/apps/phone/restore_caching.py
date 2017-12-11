from __future__ import absolute_import
import hashlib
import logging
import uuid
from casexml.apps.phone.const import RESTORE_CACHE_KEY_PREFIX, ASYNC_RESTORE_CACHE_KEY_PREFIX
from corehq.toggles import ENABLE_LOADTEST_USERS
from corehq.util.quickcache import quickcache
from dimagi.utils.couch.cache.cache_core import get_redis_default_cache

logger = logging.getLogger(__name__)


class _CacheAccessor(object):
    cache_key = None
    timeout = None
    debug_info = None

    def get_value(self):
        logger.debug('getting {}'.format(self.debug_info))
        return get_redis_default_cache().get(self.cache_key)

    def set_value(self, value, timeout=None):
        logger.debug('setting {}'.format(self.debug_info))
        if timeout is None:
            timeout = self.timeout
        get_redis_default_cache().set(self.cache_key, value, timeout=timeout)

    def invalidate(self):
        logger.debug('invalidating {}'.format(self.debug_info))
        get_redis_default_cache().delete(self.cache_key)


@quickcache(['domain', 'user_id'], timeout=24 * 60 * 60)
def get_loadtest_factor_for_user(domain, user_id):
    from corehq.apps.users.models import CouchUser, CommCareUser
    if ENABLE_LOADTEST_USERS.enabled(domain) and user_id:
        user = CouchUser.get_by_user_id(user_id, domain=domain)
        if isinstance(user, CommCareUser):
            return user.loadtest_factor or 1
    return 1


@quickcache(['domain', 'user_id'], timeout=5 * 24 * 60 * 60)
def get_fixture_freshness_token(domain, user_id):
    return uuid.uuid4().hex


class _RestoreCache(_CacheAccessor):
    prefix = None

    def __init__(self, domain, user_id, sync_log_id, device_id):
        self.cache_key = self._make_cache_key(domain, user_id, sync_log_id, device_id)
        self.debug_info = (self.__class__.__name__, domain, user_id, sync_log_id, device_id)

    @classmethod
    def _make_cache_key(cls, domain, user_id, sync_log_id, device_id):
        hashable_key = ','.join([unicode(part) for part in [
            domain,
            cls.prefix,
            user_id,
            sync_log_id or '',
            device_id or '',
            get_loadtest_factor_for_user(domain, user_id),
            get_fixture_freshness_token(domain, user_id),
        ]])
        return hashlib.md5(hashable_key).hexdigest()


class RestorePayloadPathCache(_RestoreCache):
    timeout = 24 * 60 * 60
    prefix = RESTORE_CACHE_KEY_PREFIX


class AsyncRestoreTaskIdCache(_RestoreCache):
    timeout = 24 * 60 * 60
    prefix = ASYNC_RESTORE_CACHE_KEY_PREFIX
