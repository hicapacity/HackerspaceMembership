from django import forms
from django.conf import settings
from hicap.membership.models import Maker

import yaml
import os

with open(os.path.join(settings.BASE_PATH, "membership", "profile.yaml")) as fh:
	profile_schema = yaml.load(fh)['profile']

class MakerAuthForm(forms.Form):
	username = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={"placeholder": "Username"}))
	password = forms.fields.CharField(widget=forms.widgets.PasswordInput(attrs={"placeholder": "Password"}))

class MakerProfileForm(forms.ModelForm):
	class Meta:
		model = Maker
		exclude = ('username', 'password', 'last_login', 'date_joined')

class PasswordChangeForm(forms.Form):
	old_password = forms.fields.CharField(widget=forms.widgets.PasswordInput(attrs={"placeholder": "Password"}))
	new_password = forms.fields.CharField(widget=forms.widgets.PasswordInput(attrs={"placeholder": "New Password"}))

class PasswordResetRequestForm(forms.Form):
	username = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={"placeholder": "Username"}))

class PasswordResetForm(forms.Form):
	username = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={"placeholder": "Username"}))
	nonce = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={"placeholder": "Nonce"}))
	new_password = forms.fields.CharField(widget=forms.widgets.PasswordInput(attrs={"placeholder": "New Password"}))

def create_profile_form(meta):
	_LinksFields = {}
	for field in profile_schema['links']:
		_LinksFields[field['id']] = forms.CharField(
			max_length = 255,
			required = False,
			help_text = field['prefix']
		)
	_LinksForm = type("_Form", (forms.Form,), _LinksFields)

	return _LinksForm()



