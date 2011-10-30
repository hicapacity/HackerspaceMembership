from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms
from form_utils.forms import BetterModelForm

from hicap.membership.models import Maker
from hicap.billing.models import Payment
from django.contrib.auth.models import User, UserManager

class PaymentInlineAdmin(admin.StackedInline):
	model = Payment
	extra = 0
	fieldsets = (
		(None, {
			'fields': ('payment_type', 'payment_method', 'payment_amount', 'cycle_start',),
			}),
		('Extra', {
			'classes': ('collapse',),
			'fields': ('num_cycle', 'payment_note',),
			}),
		)

class MakerAdminForm(forms.ModelForm):
	username = forms.CharField(min_length=8, max_length=30)
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
			self._errors['username'] = self.error_class(['User doesn\'t exist'])
			target_user = None

		if target_user:
			try:
				if target_user.maker.pk is not instance.pk:
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
				raise ValidationError('User doesn\'t exist')


		print self.initial['password']
		if data['password'] == '':
			print "password blank"

		if commit:
			model.save()

		return model


class MakerAdmin(admin.ModelAdmin):
	form = MakerAdminForm
	inlines = (PaymentInlineAdmin,)
	fieldsets = (
		(None, {
			'fields': ('username', 'password'),
			}),
		('Display Info', {
			'fields': ('display_name', 'email',),
			}),
		)


admin.site.register(Maker, MakerAdmin)
