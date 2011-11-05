from django.db import models
from django.core.exceptions import ValidationError
from hicap.billing.utils import add_months
import datetime

MEMBERSHIP = 'MS'
DONATION = 'DN'

CREDIT_CARD = 'CC'
PAYPAL = 'PP'
CHECK = 'CK'

TIER_STANDARD = 0
TIER_ELITE = 1

MEMBERSHIP_TIERS = (
	(TIER_STANDARD, 'Standard: $35'),
	(TIER_ELITE, 'Help Us Grow: $50'),
)

PAYMENT_METHODS = (
	(CREDIT_CARD, 'Credit Card'),
	(PAYPAL, 'Paypal'),
	(CHECK, 'Check'),
)

class Payment(models.Model):
	maker = models.ForeignKey('membership.Maker')
	payment_method = models.CharField(max_length=2, choices=PAYMENT_METHODS)
	payment_created = models.DateTimeField(default=datetime.datetime.now)
	payment_amount = models.DecimalField(max_digits = 7, decimal_places = 2, blank = True, null = True, help_text = 'USD Currency')
	payment_note = models.TextField(blank = True, help_text = 'Insert other notes here as needed (Like check number, transaction number, confirmation)')

	def __unicode__(self):
		return "Mysterious Payment"

	@classmethod
	def monthly_sum(cls, start, end):
		objs = cls.objects.filter(payment_created__gte=start, payment_created__lte=end).aggregate(sum = models.Sum('payment_amount'))
		return objs['sum']

	class Meta:
		abstract = True

class MembershipPayment(Payment):
	tier = models.IntegerField(choices=MEMBERSHIP_TIERS, default=TIER_STANDARD)
	cycle_start = models.DateField(blank = True, null = True, help_text = 'For membership only: start date for cycle this payment applies to')
	norm_cycle_end = models.DateField(blank = True, null = True)
	num_cycle = models.IntegerField(default = 1, help_text = 'If payment is for multiple months')
	enforce_cycle_integrity = models.BooleanField(default=True, help_text = 'Forces membership payment to not overlap cycles')
	auto_normalize_cycle_end = models.BooleanField(default=True, help_text = 'Automatically calculate cycle_end on save, disable if you need to manually modify that')

	def __unicode__(self):
		return "Membership: {user} {start} to {end}".format(
			user = self.maker.user,
			start = self.cycle_start,
			end = self.norm_cycle_end,
		)

	def clean(self):
		if (not self.cycle_start) or (not self.num_cycle):
			raise ValidationError('Please set cycle_start/num_cycle for membership payments')
		if self.enforce_cycle_integrity:
			pass
			#no code here yet
			#raise ValidationError('cycle_start interacts with other payment')

	def save(self, *args, **kwargs):
		if self.auto_normalize_cycle_end:
			# since object has been cleaned we expect cycle_start and num_cycle to exist
			# if not then tough, exceptions will bubble up
			start = self.cycle_start
			end = add_months(start, self.num_cycle)
			self.norm_cycle_end = end - datetime.timedelta(1)
		super(MembershipPayment, self).save(*args, **kwargs)

class Donation(Payment):
	date = models.DateField(blank = True, null = True, help_text = 'Date donation made')
	def __unicode__(self):
		return "Donation: {user} {date} for ${value}".format(
			user = self.maker.user,
			date = self.date,
			value = self.payment_amount,
		)

