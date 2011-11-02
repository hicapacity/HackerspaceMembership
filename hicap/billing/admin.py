from django.contrib import admin

from hicap.billing.models import MembershipPayment, Donation

admin.site.register(MembershipPayment)
admin.site.register(Donation)
