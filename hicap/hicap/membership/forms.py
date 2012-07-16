from django import forms
from django.conf import settings
from django.core import validators
from hicap.membership.models import Maker, profile_schema

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

def fields_from_spec(data):
	fields = {}
	for f in data:
		opts = {}
		opts['required'] = False
		opts['label'] = f['label']
		if 'type' in f:
			if f['type'] == 'tagify':
				opts['widget'] = forms.Textarea(attrs={"class":"tagify"})
			if f['type'] == 'textarea':
				opts['widget'] = forms.Textarea()
		else:
			opts['max_length'] = 255

		if 'prefix' in f:
			opts['help_text'] = f['prefix']
			
		fields[f['id']] = forms.CharField(**opts)
	return fields

def create_profile_form():
	_InfoForm = type(
		"_InfoFields",
		(forms.Form,),
		fields_from_spec(profile_schema['info'])
	)

	_TagsForm = type(
		"_TagsForm",
		(forms.Form,),
		fields_from_spec(profile_schema['tags'])
	)

	_LinksForm = type(
		"_LinksForm",
		(forms.Form,),
		fields_from_spec(profile_schema['links'])
	)

	return _InfoForm, _LinksForm, _TagsForm



