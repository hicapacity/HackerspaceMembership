from django.db import models
from django.contrib.auth.models import User
import datetime
from hicap.billing.models import MembershipPayment

class Maker(models.Model):
	user = models.OneToOneField(User)
	email = models.EmailField(unique=True)
	display_name = models.CharField(max_length=255)

	def __unicode__(self):
		return "{name} ({user})".format(name=self.display_name, user=self.user.username)

	def is_current(self, date = None):
		if date is None:
			date = datetime.datetime.now()

		objs = self.membershippayment_set.filter(cycle_start__lte=date, norm_cycle_end__gte=date)
		if len(objs):
			return True
		return False

	@staticmethod
	def active_members(date):
		objs = MembershipPayment.objects.filter(cycle_start__lte=date, norm_cycle_end__gte=date)
		return len(objs)
