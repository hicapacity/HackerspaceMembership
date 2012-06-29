from django.db import models
from django.core.exceptions import ValidationError
from hicap.billing.utils import add_months
from hicap.utils import to_unixtime
from datetime import datetime, timedelta
import json
import logging
import decimal
from functools import partial

UNKNOWN = '??'
MEMBERSHIP = 'MS'
DONATION = 'DN'

PAYMENT_TYPES = (
	(MEMBERSHIP, 'Membership Fee'),
	(DONATION, 'Donation'),
  (UNKNOWN, 'Other'),
)

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
	PAYMENT_TYPE = UNKNOWN

	maker = models.ForeignKey('membership.Maker')
	payment_method = models.CharField(max_length=2, choices=PAYMENT_METHODS)
	payment_created = models.DateTimeField(default=datetime.now)
	payment_amount = models.DecimalField(max_digits = 7, decimal_places = 2, blank = True, null = True, help_text = 'USD Currency')
	payment_note = models.TextField(blank = True, help_text = 'Insert other notes here as needed (Like check number, transaction number, confirmation)')
	payment_identifier = models.CharField(max_length=255, blank=True)

	def __unicode__(self):
		return "Mysterious Payment"

	@classmethod
	def monthly_sum(cls, start, end):
		objs = cls.objects.filter(payment_created__gte=start, payment_created__lte=end).aggregate(sum = models.Sum('payment_amount'))
		return objs['sum']

	@property
	def forJSON(self):
		return {
			'id': self.pk,
			'maker': self.maker.pk,
			'created': to_unixtime(self.payment_created),
			'start': to_unixtime(self.cycle_start),
			'end': to_unixtime(self.norm_cycle_end),
		}

	class Meta:
		abstract = True

class MembershipPayment(Payment):
	PAYMENT_TYPE = MEMBERSHIP

	tier = models.IntegerField(choices=MEMBERSHIP_TIERS, default=TIER_STANDARD)
	cycle_start = models.DateField(blank = True, null = True, help_text = 'For membership only: start date for cycle this payment applies to')
	norm_cycle_end = models.DateField(blank = True, null = True)
	num_cycle = models.IntegerField(default = 1, help_text = 'If payment is for multiple months')
	auto_normalize_cycle_end = models.BooleanField(default=True, help_text = 'Automatically calculate cycle_end on save, disable if you need to manually modify that')

	def __unicode__(self):
		return "Membership: {username} ({value}) {start} to {end}".format(
			username = self.maker.username,
			value = self.payment_amount,
			start = self.cycle_start,
			end = self.norm_cycle_end,
		)

	def clean(self):
		if not self.cycle_start:
			self.cycle_start = self.get_next_cycle()
		if not self.num_cycle:
			raise ValidationError('Please set num_cycle for membership payments')

	def save(self, *args, **kwargs):
		if self.auto_normalize_cycle_end:
			# since object has been cleaned we expect cycle_start and num_cycle to exist
			# if not then tough, exceptions will bubble up
			start = self.cycle_start
			end = add_months(start, self.num_cycle)
			self.norm_cycle_end = end - timedelta(1)
		super(MembershipPayment, self).save(*args, **kwargs)

	def get_next_cycle(self):
		try:
			obj = MembershipPayment.objects.all().order_by('-cycle_start')[0]
			ret = obj.norm_cycle_end
			return ret
		except IndexError:
			return datetime.now()

class Donation(Payment):
	PAYMENT_TYPE = DONATION

	date = models.DateField(blank = True, null = True, help_text = 'Date donation made')
	def __unicode__(self):
		return "Donation: {username} {date} for ${value}".format(
			username = self.maker.username,
			date = self.date,
			value = self.payment_amount,
		)

class PaymentLog(models.Model):
	created = models.DateTimeField(default=datetime.now)
	payment_method = models.CharField(max_length=2, choices=PAYMENT_METHODS)
	payment_id = models.IntegerField(blank=True, null=True)
	payment_amount = models.DecimalField(max_digits = 7, decimal_places = 2, blank = True, null = True, help_text = 'USD Currency')
	payment_note = models.TextField(blank = True, help_text = 'Insert other notes here as needed')
	payment_data = models.TextField(blank = True, help_text = 'Associated data')
	
	@staticmethod
	def make_from_payment(payment, note):
		pl = PaymentLog()
		for cls in [MembershipPayment, Donation]:
			if isinstance(payment, cls):
				pl.payment_method = cls.PAYMENT_TYPE
				pl.payment_id = payment.id
				break
		else:
			pl.payment_method = UNKNOWN
			pl.payment_id = None
		pl.payment_amount = payment.payment_amount
		pl.payment_note = note
		pl.save()

class DecimalEnabledEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, decimal.Decimal):
			return str(obj)
		return json.JSONEncoder.default(self, obj)

def log_ipn(sender, **kwargs):
	logging.error("in log_ipn")
	try:
		logging.error(sender)
		ipn_obj = sender
		log_msg = {}
		for i in ['txn_type', 'custom', 'parent_txn_id', 'txn_id', 'payer_id', 'payer_email', 'first_name', 'last_name', 'payment_gross', 'payment_status', 'payment_type', 'pending_reason', 'reason_code']:
			if hasattr(ipn_obj, i):
				log_msg[i] = getattr(ipn_obj, i, None)
		log_msg['dir'] = dir(ipn_obj)
		pl = PaymentLog()
		pl.payment_note = kwargs.get('_signal_name', 'Some mysterious payment log')
		pl.payment_data = json.dumps(log_msg, cls=DecimalEnabledEncoder)
		pl.save()
		logging.error("success")
	except Exception as e:
		logging.error(e)

def create_from_ipn(sender, **kwargs):
	from hicap.membership.models import Maker
	ipn_obj = sender
	try:
		m = Maker.objects.get(email=getattr(ipn_obj, 'payer_email', None))
	except Maker.DoesNotExist:
		email = getattr(ipn_obj, 'payer_email', None)
		username = email
		m = Maker(
			username = email,
			email = email,
			first_name = getattr(ipn_obj, 'first_name', 'First Name'),
			last_name = getattr(ipn_obj, 'last_name', 'Last Name')
		)
		m.save()
	amount = decimal.Decimal(getattr(ipn_obj, 'payment_amount', '0.00'))
	txn_id = getattr(ipn_obj, 'txn_id', None)
	tier = TIER_ELITE if (amount >= 50) else TIER_STANDARD
	p = MembershipPayment(
		maker = m,
		payment_method = PAYPAL,
		payment_created = datetime.now(),
		payment_amount = amount,
		payment_note = "Imported from paypal ipn",
		payment_identifier = txn_id,
		tier = tier,
		cycle_start = datetime.now(),
		num_cycle = 1,
	)
	p.save()
	print p
			
from paypal.standard.ipn.signals import payment_was_successful
payment_was_successful.connect(partial(log_ipn, _signal_name="Payment was successful"), weak=False)
payment_was_successful.connect(create_from_ipn, weak=False)

from paypal.standard.ipn.signals import payment_was_flagged
from paypal.standard.ipn.signals import subscription_cancel
from paypal.standard.ipn.signals import subscription_eot
from paypal.standard.ipn.signals import subscription_modify
from paypal.standard.ipn.signals import subscription_signup
