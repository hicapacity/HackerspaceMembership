from django.core.management.base import BaseCommand, CommandError
from collections import namedtuple
import csv
import sys

from hicap.billing.models import Payment, Donation
from hicap.membership.models import Maker

FauxMember = namedtuple('FauxMember', ['name', 'email'])
FauxPayment = namedtuple('FauxPayment', ['value', 'date', 'time', 'transaction_id'])

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
					p = FauxPayment(value=row.get('GROSS'), date=row.get('DATE'), time=row.get('TIME'), transaction_id=row.get('TRANSACTION ID'))
					if m.name in MEMBERS_TO_IGNORE:
						continue
					if row.get('TYPE') not in TYPE_WHITELIST:
						continue
					if m not in members:
						members[m] = []
					members[m].append(p)

		all_members_in = True
		for member in members.keys():
			try:
				m = Maker.objects.get(email=member.email)
			except Maker.DoesNotExist:
				sys.stderr.write("Plz create acct for: {name} ({email})\n".format(name=member.name, email=member.email))
				all_members_in = False

		if not all_members_in:
			sys.stderr.write("No proceeding with imports until this is taken care of.\n")
			return
