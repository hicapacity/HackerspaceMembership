from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from collections import namedtuple
from datetime import datetime
import sys
import re
import decimal

import paypal
from hicap.billing.models import MembershipPayment, PAYPAL, TIER_STANDARD, TIER_ELITE
from hicap.membership.models import Maker

extract = re.compile(r'L_(\D+)(\d+)')

def to_paypal_timestamp(utc):
	return utc.strftime("%Y-%m-%dT%H:%M:%SZ")

def from_paypal_timestamp(s):
	return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

def make_payment(obj):
	txn_id = obj.get('TRANSACTIONID')
	email = obj.get('EMAIL')
	amount = decimal.Decimal(obj.get('AMT', '0.00'))
	if amount <= 0:
		return
	if obj.get('STATUS') != 'Completed':
		return
	if email is None:
		print "NO EMAIL"
		print obj
		return
	try:
		p = MembershipPayment.objects.get(payment_identifier=txn_id)
		print "skipping"
		return
	except MembershipPayment.DoesNotExist:
		pass	
	try:
		m = Maker.objects.get(email=email)
	except Maker.DoesNotExist:
		m = Maker(
			username = email,
			email = email,
			first_name = obj.get('NAME'),
		)
		m.save()
	tier = TIER_ELITE if (amount >= 50) else TIER_STANDARD
	p = MembershipPayment(
		maker = m,
		payment_method = PAYPAL,
		payment_created = datetime.utcnow(),
		payment_amount = amount,
		payment_note = "Imported from paypal CLI",
		payment_identifier = txn_id,
		tier = tier,
		cycle_start = from_paypal_timestamp(obj.get('TIMESTAMP')),
		num_cycle = 1,
	)
	p.save()
	print p

class Command(BaseCommand):
	args = '<input_file>'
	help = 'Import paypal payments from api'

	def handle(self, *args, **options):
		ppc = paypal.PayPalConfig(
			API_USERNAME = settings.PAYPAL_API_USERNAME,
			API_PASSWORD = settings.PAYPAL_API_PASSWORD,
			API_SIGNATURE = settings.PAYPAL_API_SIGNATURE,
			DEBUG_LEVEL = 0,
			API_ENVIRONMENT = "PRODUCTION",
			HTTP_TIMEOUT = 60,
		)
		ppi = paypal.PayPalInterface(config=ppc)

		utcnow = datetime.utcnow()
		start = '2011-05-04T01:39:07Z'
		end = None

		while 1:
			start_dt = from_paypal_timestamp(start)
			res = ppi._call('TransactionSearch', StartDate=start, EndDate=end)
			items = {}
			for k in (i for i in res.raw.keys() if i.startswith('L_')):
				_type, i = extract.match(k).groups()
				i = int(i)
				if i not in items:
					items[i] = {}
				items[i][_type] = res[k]
			print "Got {0} items".format(len(items))
			for i in sorted(items.keys()):
				make_payment(items[i])

			if len(items) <= 1:
				break

			end = items[i]['TIMESTAMP']
		sys.stderr.write("done\n")
