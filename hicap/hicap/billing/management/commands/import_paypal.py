from django.core.management.base import BaseCommand, CommandError
from collections import namedtuple
from datetime import datetime
import csv
import sys

from hicap.billing.models import MembershipPayment, Donation, TIER_STANDARD, TIER_ELITE, PAYPAL
from hicap.membership.models import Maker

class FauxMember(object):
	def __init__(self, name, email):
		self.name = name
		self.email = email
		self.username = None
		self.payments = []

FauxPayment = namedtuple('FauxPayment', ['value', 'date', 'time', 'datetime', 'transaction_id'])

MEMBERS_TO_IGNORE = ['GoFundMe', 'Bank Account']
TYPE_WHITELIST = ['Payment Received', 'Recurring Payment Received']

class Command(BaseCommand):
	args = '<input_file>'
	help = 'Import tab-delimited paypal dump into db'

	def handle(self, *args, **options):
		members = dict()
		for fn in args:
			with open(fn) as fh:
				reader = csv.DictReader(fh, dialect="excel-tab")
				for _row in reader:
					# need to clean up this bad dict
					row = dict((k.strip().upper(), v) for k,v in _row.iteritems())
					m = FauxMember(name=row.get('NAME'), email=row.get('FROM EMAIL ADDRESS'))
					dt = datetime.strptime(
						"{d} {t}".format(d=row.get('DATE'), t=row.get('TIME')),
						"%m/%d/%Y %H:%M:%S",
					)
					p = FauxPayment(value=row.get('GROSS'), date=row.get('DATE'), time=row.get('TIME'), datetime=dt, transaction_id=row.get('TRANSACTION ID'))
					if m.name in MEMBERS_TO_IGNORE:
						continue
					if row.get('TYPE') not in TYPE_WHITELIST:
						continue
					if m.name not in members:
						members[m.name] = m
					members[m.name].payments.append(p)

		# create or associate items with database
		for member in members.values():
			try:
				m = Maker.objects.get(email=member.email)
				member.username = m.username
				sys.stderr.write("{name} ({email}) -> {username}\n".format(name=member.name, email=member.email, username=member.username))
			except Maker.DoesNotExist:
				member.username = member.name.lower().replace(' ' , '.')
				first, last = (member.name.split(' ', 1) + ["", ""])[:2]
				m = Maker(username=member.username, first_name = first, last_name = last, email = member.email)
				m.save()
				sys.stderr.write("{name} ({email}) -> NEW {username}\n".format(name=member.name, email=member.email, username=member.username))

		# okay, import payments
		for member in members.values():
			m = Maker.objects.get(email=member.email)
			print m
			for payment in member.payments:
				tier = TIER_ELITE
				p = MembershipPayment(
					maker = m,
					payment_method = PAYPAL,
					payment_created = payment.datetime,
					payment_amount = float(payment.value.replace(',','')),
					payment_note = "Imported from paypal csv",
					tier = tier,
					cycle_start = payment.datetime,
					num_cycle = 1,
				)
				p.save()
				print p
