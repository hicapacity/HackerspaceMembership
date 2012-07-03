from django.db import models
from django.contrib.auth.models import User
from django.contrib import messages
import datetime
from hicap.billing.models import MembershipPayment
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save

class Maker(models.Model):
	username = models.CharField(_('username'), max_length=255, unique=True, help_text=_("Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters"))
	first_name = models.CharField(_('first name'), max_length=255, blank=True)
	last_name = models.CharField(_('last name'), max_length=255, blank=True)
	email = models.EmailField(_('e-mail address'), blank=True)
	password = models.CharField(_('password'), max_length=255, help_text=_("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))
	last_login = models.DateTimeField(_('last login'), default=datetime.datetime.now)
	date_joined = models.DateTimeField(_('date joined'), default=datetime.datetime.now)

	get_full_name = User.__dict__['get_full_name']
	set_password = User.__dict__['set_password']
	check_password = User.__dict__['check_password']
	email_user = User.__dict__['email_user']
	is_authenticated = User.__dict__['is_authenticated']

	#_shadowed_user : Memoized value of associated admin user (if it exists)
	#_password_set : Temporary store for assigned password

	def __unicode__(self):
		return self.username

	def save(self, *args, **kwargs):
		self.maker_password_set = None
		if self.password == "":
			password = User.objects.make_random_password()
			self.set_password(password)
			self._password_set = password
		else:
			try:
				faux_maker = Maker.objects.get(pk=self.pk)
				prev_password = faux_maker.password
			except Maker.DoesNotExist:
				prev_password = ""
			if prev_password != self.password:
				self.set_password(self.password)
		super(Maker, self).save(*args, **kwargs)

	def is_current(self, date = None):
		if date is None:
			date = datetime.datetime.now()

		objs = self.membershippayment_set.filter(cycle_start__lte=date, norm_cycle_end__gte=date)
		if len(objs):
			return True
		return False

	def last_cycle_end(self):
		try:
			obj = self.membershippayment_set.latest('norm_cycle_end')
			return obj.norm_cycle_end
		except MembershipPayment.DoesNotExist:
			return None

	@property
	def is_active(self):
		if self.associated_user:
			return self.associated_user.is_active
		return False

	@property
	def is_staff(self):
		if self.associated_user:
			return self.associated_user.is_staff
		return False

	def has_perm(self, perm, obj=None):
		if self.associated_user:
			return self.associated_user.has_perm(perm, obj)
		return False

	def has_module_perms(self, package_name):
		if self.associated_user:
			return self.associated_user.has_module_perms(package_name)
		return False

	@property
	def associated_user(self):
		if not hasattr(self, "_shadowed_user"):
			try:
				user = User.objects.get(username=self.username)
				self._shadowed_user = user
			except User.DoesNotExist:
				self._shadowed_user = None
		return self._shadowed_user

	@staticmethod
	def active_members(date):
		objs = MembershipPayment.objects.filter(cycle_start__lte=date, norm_cycle_end__gte=date)
		return len(objs)

	@property
	def forJSON(self):
		return {
			'id': self.pk,
			'name': self.get_full_name(),
			'email': self.email,
		}



def on_post_save(instance, **kwargs):
	if instance.maker_password_set is not None:
		pass

post_save.connect(
	on_post_save,
	dispatch_uid = "maker_post_save",
	sender = Maker,
	weak = False,
)
