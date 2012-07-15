from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms
from form_utils.forms import BetterModelForm

from hicap.membership.models import Maker, ProfileInfo
from hicap.billing.models import MembershipPayment, Donation

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

class MakerAdmin(admin.ModelAdmin):
	form = MakerAdminForm
	inlines = (MembershipPaymentInlineAdmin, DonationInlineAdmin)
	fieldsets = (
		(None, {
			'fields': ('username', 'password'),
			}),
		('Display Info', {
			'fields': ('first_name', 'last_name', 'email',),
			}),
		('Options', {
			'fields': ('publish_membership',),
			}),
		)

admin.site.register(Maker, MakerAdmin)
admin.site.register(ProfileInfo)

