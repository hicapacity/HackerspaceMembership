from django.contrib import admin

from hicap.billing.models import MembershipPayment, Donation, PaymentLog

admin.site.register(MembershipPayment)
admin.site.register(Donation)
admin.site.register(PaymentLog)
