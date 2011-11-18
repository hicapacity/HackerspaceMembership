from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms
from form_utils.forms import BetterModelForm

from hicap.membership.models import Maker
from hicap.billing.models import MembershipPayment, Donation
from django.contrib.auth.models import User, UserManager

class DonationInlineAdmin(admin.StackedInline):
	model = Donation
	extra = 0
	fieldsets = (
	(None, {
		'fields': ('payment_method', 'payment_amount', 'date',),
		}),
	('Extra', {
		'classes': ('collapse',),
		'fields': ('payment_note', 'payment_created'),
		}),
	)

class MembershipPaymentInlineAdmin(admin.StackedInline):
	model = MembershipPayment
	extra = 0
	fieldsets = (
		(None, {
			'fields': ('tier', 'payment_method', 'payment_amount', 'cycle_start',),
			}),
		('Extra', {
			'classes': ('collapse',),
			'fields': ('num_cycle', 'payment_note', 'payment_created'),
			}),
		)

class MakerAdminForm(forms.ModelForm):
	username = forms.CharField(max_length=30)
	password = forms.CharField(required=False, help_text="Set blank to autogenerate")
	class Meta:
		model = Maker

	def __init__(self, *args, **kwargs):
		super(MakerAdminForm, self).__init__(*args, **kwargs)
		if 'instance' in kwargs:
			instance = kwargs['instance']
			self.initial['username'] = instance.user.username
			self.initial['password'] = instance.user.password

	def clean(self):
		cleaned_data = super(MakerAdminForm, self).clean()

		instance = self.instance

		try:
			target_user = User.objects.get(username=cleaned_data['username'])
		except User.DoesNotExist:
			target_user = None
		except KeyError:
			target_user = None

		if target_user:
			try:
				if target_user.maker.pk != instance.pk:
					self._errors['username'] = self.error_class(['User already has profile'])
			except Maker.DoesNotExist:
				pass

		return cleaned_data

	def save(self, commit=True):
		data = self.cleaned_data
		model = super(MakerAdminForm, self).save(commit=False)

		try:
			user = model.user
		except User.DoesNotExist:
			try:
				user = User.objects.get(username=data['username'])
				model.user = user
			except User.DoesNotExist:
				user = User()
				user.username = data['username']
				if 'password' in data:
					password = data['password']
				else:
					password = UserManager.make_random_password()
				user.set_password(password)
				user.save()
				model.user = user

		if commit:
			model.save()

		return model


class MakerAdmin(admin.ModelAdmin):
	form = MakerAdminForm
	inlines = (MembershipPaymentInlineAdmin, DonationInlineAdmin)
	fieldsets = (
		(None, {
			'fields': ('username', 'password'),
			}),
		('Display Info', {
			'fields': ('display_name', 'email',),
			}),
		)

admin.site.register(Maker, MakerAdmin)

