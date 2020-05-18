import re

from django import forms
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from crispy_forms import bootstrap as twbscrispy
from crispy_forms import layout as crispy
from email_validator import EmailNotValidError, validate_email

from corehq.apps.hqwebapp import crispy as hqcrispy
from corehq.motech.const import PASSWORD_PLACEHOLDER
from corehq.motech.models import ConnectionSettings


class ConnectionSettingsForm(forms.ModelForm):
    url = forms.CharField(
        label=_('URL'),
        help_text=_('e.g. "https://play.dhis2.org/dev/"')
    )
    username = forms.CharField(required=False)
    plaintext_password = forms.CharField(
        label=_('Password'),
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    skip_cert_verify = forms.BooleanField(
        label=_('Skip certificate verification'),
        help_text=_('Do not use in a production environment'),
        required=False,
    )
    notify_addresses_str = forms.CharField(
        label=_('Addresses to send notifications'),
        help_text=_('A comma-separated list of email addresses to send error '
                    'notifications'),
        required=False,
    )

    class Meta:
        model = ConnectionSettings
        fields = [
            'name',
            'url',
            'auth_type',
            'username',
            'plaintext_password',
            'skip_cert_verify',
            'notify_addresses_str',
        ]

    def __init__(self, domain, *args, **kwargs):
        from corehq.motech.views import ConnectionSettingsListView

        if kwargs.get('instance') and kwargs['instance'].plaintext_password:
            # `plaintext_password` is not a database field, and so
            # super().__init__() will not update `initial` with it. We
            # need to do that here.
            #
            # We use PASSWORD_PLACEHOLDER to avoid telling the user what
            # the password is, but still indicating that it has been
            # set. (The password is only changed if its value is not
            # PASSWORD_PLACEHOLDER.)
            if 'initial' in kwargs:
                kwargs['initial']['plaintext_password'] = PASSWORD_PLACEHOLDER
            else:
                kwargs['initial'] = {'plaintext_password': PASSWORD_PLACEHOLDER}
        super().__init__(*args, **kwargs)

        self.domain = domain
        self.helper = hqcrispy.HQFormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3 col-md-2'
        self.helper.field_class = 'col-sm-9 col-md-8 col-lg-6'
        self.helper.offset_class = 'col-sm-offset-3 col-md-offset-2'
        self.helper.layout = crispy.Layout(
            crispy.Fieldset(
                _('Remote API Connection'),
                crispy.Field('name'),
                crispy.Field('url'),
                crispy.Field('auth_type'),
                crispy.Field('username'),
                crispy.Field('plaintext_password'),
                twbscrispy.PrependedText('skip_cert_verify', ''),
                crispy.Field('notify_addresses_str'),
            ),
            hqcrispy.FormActions(
                twbscrispy.StrictButton(
                    _("Save"),
                    type="submit",
                    css_class="btn btn-primary",
                ),
                hqcrispy.LinkButton(
                    _("Cancel"),
                    reverse(
                        ConnectionSettingsListView.urlname,
                        kwargs={'domain': self.domain},
                    ),
                    css_class="btn btn-default",
                ),
            ),
        )

    def clean_notify_addresses_str(self):
        emails = self.cleaned_data['notify_addresses_str']
        are_valid = (validate_email(e) for e in re.split('[, ]+', emails) if e)
        try:
            all(are_valid)
        except EmailNotValidError:
            raise forms.ValidationError(_("Contains an invalid email address."))
        return emails

    def save(self, commit=True):
        self.instance.domain = self.domain
        self.instance.plaintext_password = self.cleaned_data['plaintext_password']
        return super().save(commit)
