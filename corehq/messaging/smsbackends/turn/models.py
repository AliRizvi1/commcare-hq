from collections import namedtuple

from corehq.apps.sms.models import SQLSMSBackend
from corehq.apps.sms.util import clean_phone_number
from corehq.messaging.smsbackends.turn.exceptions import WhatsAppTemplateStringException
from corehq.messaging.smsbackends.turn.forms import TurnBackendForm
from turn import TurnBusinessManagementClient, TurnClient
from turn.exceptions import WhatsAppContactNotFound

WA_TEMPLATE_STRING = "cc_wa_template"


class SQLTurnWhatsAppBackend(SQLSMSBackend):
    class Meta(object):
        proxy = True
        app_label = "sms"

    @classmethod
    def get_api_id(cls):
        return "TURN"

    @classmethod
    def get_generic_name(cls):
        return "Turn.io"

    @classmethod
    def get_available_extra_fields(cls):
        return [
            "template_namespace",
            "client_auth_token",
            "business_id",
            "business_auth_token",
        ]

    @classmethod
    def get_form_class(cls):
        return TurnBackendForm

    def send(self, msg, orig_phone_number=None, *args, **kwargs):
        config = self.config
        client = TurnClient(config.client_auth_token)
        to = clean_phone_number(msg.phone_number)

        try:
            wa_id = client.contacts.get_whatsapp_id(to)
        except WhatsAppContactNotFound:
            pass  # TODO: Fallback to SMS?

        if is_whatsapp_template_message(msg.text):
            return self._send_template_message(client, wa_id, msg.text)
        else:
            return self._send_text_message(client, wa_id, msg.text)

    def _send_template_message(self, client, wa_id, message_text):
        parts = get_template_hsm_parts(message_text)
        try:
            return client.messages.send_templated_message(
                wa_id,
                self.config.template_namespace,
                parts.template_name,
                parts.lang_code,
                parts.params,
            )
        except:  # TODO: Add messaging exceptions to package
            raise

    def _send_text_message(self, client, wa_id, message_text):
        try:
            return client.messages.send_text(wa_id, message_text)
        except:  # TODO: Add message exceptions to package
            raise

    def get_all_templates(self):
        config = self.config
        client = TurnBusinessManagementClient(config.business_id, config.business_auth_token)
        return client.message_templates.get_message_templates()


def is_whatsapp_template_message(message_text):
    return message_text.lower().startswith(WA_TEMPLATE_STRING)


def get_template_hsm_parts(message_text):
    HsmParts = namedtuple("hsm_parts", "template_name lang_code params")
    parts = message_text.split("~")[0].split(":")

    try:
        params = [p.strip() for p in parts[3].split(",")]
    except IndexError:
        params = []

    try:
        return HsmParts(template_name=parts[1], lang_code=parts[2], params=params)
    except IndexError:
        raise WhatsAppTemplateStringException


def generate_template_string(template):
    """From the template JSON returned by Turn, create the magic string for people to copy / paste
    """

    template_text = ""
    for component in template.get('components', []):
        if component.get("type") == "BODY":
            template_text = component.get("text", "")
            break
    num_params = template_text.count('{') // 2  # each parameter is bracketed by {{}}
    parameters = ",".join([f'{{var{i}}}' for i in range(1, num_params + 1)])
    return f"{WA_TEMPLATE_STRING}:{template['name']}:{template['language']}:{parameters}~"
