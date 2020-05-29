from django.test import SimpleTestCase

import requests_mock

from corehq.apps.sms.models import QueuedSMS
from corehq.messaging.smsbackends.trumpia.models import (
    TrumpiaBackend,
    TrumpiaRetry,
)


USERNAME = "testuser"
API_KEY = "123456789abc1011"


class TestTrumpiaBackend(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = TrumpiaBackend()
        cls.backend.extra_fields = {"username": USERNAME, "api_key": API_KEY}

    def test_success(self):
        msg = self.mock_send()
        self.assertEqual(msg.backend_message_id, "1234561234567asdf123")
        self.assertIsNone(msg.system_error_message)
        self.assertFalse(msg.error)

    def test_success_MRCE0000(self):
        msg = self.mock_send(response={
            "request_id": "1234561234567asdf123",
            "status_code": "MRCE0000",
        })
        self.assertEqual(msg.backend_message_id, "1234561234567asdf123")
        self.assertIsNone(msg.system_error_message)
        self.assertFalse(msg.error)

    def test_success_MPCE4001(self):
        msg = self.mock_send(response={
            "request_id": "1234561234567asdf123",
            "status_code": "MPCE4001",
        })
        self.assertEqual(msg.backend_message_id, "1234561234567asdf123")
        self.assertIsNone(msg.system_error_message)
        self.assertFalse(msg.error)

    def test_fail_MPCE4001(self):
        # missing request_id -> error
        msg = self.mock_send(response={"status_code": "MPCE4001"})
        self.assertIsNone(msg.backend_message_id)
        self.assertEqual(msg.system_error_message, "Gateway error: MPCE4001")
        self.assertTrue(msg.error)

    def test_error_status_code(self):
        msg = self.mock_send(response={"status_code": "MRCE0101"})
        self.assertIsNone(msg.backend_message_id)
        self.assertEqual(msg.system_error_message, "Gateway error: MRCE0101")
        self.assertTrue(msg.error)

    def test_blocked_mobile(self):
        msg = self.mock_send(response={
            "status": "failed",
            "blocked_mobile": {"number": "2003004000"},
        })
        self.assertIsNone(msg.backend_message_id)
        self.assertEqual(msg.system_error_message, "Gateway error: blocked")
        self.assertTrue(msg.error)

    def test_retry_MPCE0301(self):
        with self.assertRaises(TrumpiaRetry) as err:
            self.mock_send(response={"status_code": "MPCE0301"})
        self.assertRegex(str(err.exception), "Gateway error: MPCE0301")

    def test_retry_MRCE0301(self):
        with self.assertRaises(TrumpiaRetry) as err:
            self.mock_send(response={"status_code": "MRCE0301"})
        self.assertRegex(str(err.exception), "Gateway error: MRCE0301")

    def test_retry_MPCE0302(self):
        with self.assertRaises(TrumpiaRetry) as err:
            self.mock_send(response={"status_code": "MPCE0302"})
        self.assertRegex(str(err.exception), "Gateway error: MPCE0302")

    def test_unknown_error(self):
        msg = self.mock_send(response={"unexpected": "result"})
        self.assertIsNone(msg.backend_message_id)
        self.assertEqual(msg.system_error_message,
            'Gateway error: {"unexpected": "result"}')
        self.assertTrue(msg.error)

    def test_405(self):
        msg = self.mock_send(status_code=405)
        self.assertEqual(msg.system_error_message, "Gateway error: 405")
        self.assertTrue(msg.error)

    def test_500(self):
        with self.assertRaises(TrumpiaRetry) as err:
            self.mock_send(status_code=500)
        self.assertRegex(str(err.exception), "Gateway 500 error")

    def mock_send(self, status_code=200, response=None):
        msg = QueuedSMS(phone_number='+15554443333', text="the message")
        msg.save = lambda: None  # prevent db access in SimpleTestCase
        url = f"http://api.trumpia.com/rest/v1/{USERNAME}/sms"
        headers = {"X-ApiKey": API_KEY, "Content-Type": "application/json"}
        if response is None:
            response = {
                "request_id": "1234561234567asdf123",
                "sms_id": 987987987987
            }
        with requests_mock.Mocker() as mock:
            mock.put(
                url,
                request_headers=headers,
                status_code=status_code,
                json=(response if status_code == 200 else {})
            )
            self.backend.send(msg)
        return msg
