from django.db import models
from django.core.exceptions import ValidationError
from hicap.billing.utils import add_months
import datetime

MEMBERSHIP = 'MS'
DONATION = 'DN'

CREDIT_CARD = 'CC'
PAYPAL = 'PP'
CHECK = 'CK'

PAYMENT_TYPES = (
	(MEMBERSHIP, 'Membership'),
	(DONATION, 'Donation'),
)
PAYMENT_METHODS = (
	(CREDIT_CARD, 'Credit Card'),
	(PAYPAL, 'Paypal'),
	(CHECK, 'Check'),
)

# Create your models here.
class Payment(models.Model):
	maker = models.ForeignKey('membership.Maker')
	payment_type = models.CharField(max_length=2, choices=PAYMENT_TYPES, default=MEMBERSHIP)
	payment_method = models.CharField(max_length=2, choices=PAYMENT_METHODS)
	payment_created = models.DateTimeField(auto_now_add=True)
	cycle_start = models.DateField(blank = True, null = True, help_text = 'For membership only: start date for cycle this payment applies to')
	norm_cycle_end = models.DateField(blank = True, null = True)
	num_cycle = models.IntegerField(default = 1, help_text = 'If payment is for multiple months')
	payment_amount = models.DecimalField(max_digits = 7, decimal_places = 2, blank = True, null = True, help_text = 'USD Currency')
	payment_note = models.TextField(blank = True, help_text = 'Insert other notes here as needed (Like check number, transaction number, confirmation)')

	def __unicode__(self):
		if self.payment_type == MEMBERSHIP:
			return "Membership: {user} {start} to {end}".format(
				user = self.maker.user,
				start = self.cycle_start,
				end = self.norm_cycle_end,
			)
		if self.payment_type == DONATION:
			return "Donation: {user} {start} for ${value}".format(
				user = self.maker.user,
				start = self.cycle_start,
				value = self.payment_amount,
			)
		return "Mysterious Payment"

	def clean(self):
		if self.payment_type == MEMBERSHIP:
			if (not self.cycle_start) or (not self.num_cycle):
				raise ValidationError('Please set cycle_start/num_cycle for membership payments')

	def save(self, *args, **kwargs):
		if self.payment_type == MEMBERSHIP:
			# since object has been cleaned we expect cycle_start and num_cycle to exist
			# if not then tough, exceptions will bubble up
			start = self.cycle_start
			end = add_months(start, self.num_cycle)
			self.norm_cycle_end = end - datetime.timedelta(1)
		super(Payment, self).save(*args, **kwargs)
