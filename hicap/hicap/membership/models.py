from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
import datetime
import uuid
from hicap.billing.models import MembershipPayment
from hicap.membership.email import send_password_reset
from hicap.utils import AttrDict

from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save

import yaml
import os

with open(os.path.join(settings.BASE_PATH, "membership", "profile.yaml")) as fh:
	profile_schema = yaml.load(fh)['profile']


class Maker(models.Model):
	username = models.CharField(_('username'), max_length=255, unique=True, help_text=_("Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters"))
	first_name = models.CharField(_('first name'), max_length=255, blank=True)
	last_name = models.CharField(_('last name'), max_length=255, blank=True)
	email = models.EmailField(_('e-mail address'), blank=True)
	password = models.CharField(_('password'), max_length=255, help_text=_("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))
	last_login = models.DateTimeField(_('last login'), default=datetime.datetime.now)
	date_joined = models.DateTimeField(_('date joined'), default=datetime.datetime.now)
	publish_membership = models.BooleanField(_('Publish Membership'), default=False)

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
		self._password_set = None
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
				self._password_set = self.password
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

	@property
	def is_public(self):
		print self.publish_membership
		return self.publish_membership

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

	def send_password_reset(self):
		rn = ResetNonce.create_for_maker(self)
		send_password_reset(rn)

	@property
	def profile_data(self):
		return ProfileDataManager(self, self.profileinfo_set.all())

class ResetNonce(models.Model):
	maker = models.ForeignKey(Maker)
	nonce = models.CharField(max_length=255)
	created = models.DateTimeField(_('created'), default=datetime.datetime.now)
	
	@staticmethod
	def create_for_maker(maker):
		rn = ResetNonce(maker=maker)
		rn.nonce = str(uuid.uuid4())
		rn.save()
		return rn

class ProfileInfo(models.Model):
	maker = models.ForeignKey(Maker)
	key = models.CharField(max_length=255)
	value = models.TextField()

	def __unicode__(self):
		return "{name}: {key} -> {value}".format(
			name = self.maker.username,
			key = self.key,
			value = self.value
		)

class ProfileDataManager(object):
	def __init__(self, maker, data):
		self.maker = maker
		self._queryset = data
		self._data = dict((i.key, i.value) for i in data)
		self.has_changed = False

	@property
	def data(self):
		return self._data

	def update(self, name, value):
		if name not in self.data and value not in ('', None):
			self.data[name] = value
			pi = ProfileInfo(
				maker = self.maker,
				key = name,
				value = value
			)
			pi.save()
		elif name in self.data and self.data[name] != value:
			pi = ProfileInfo.objects.get(maker=self.maker, key=name)
			if value != '':
				pi.value = value
				pi.save()
			else:
				pi.delete()
		else:
			pass

	@property
	def info(self):
		ret = {}
		for field in profile_schema['info']:
			if field['id'] not in self.data:
				continue
			ret[field['id']] = {
				'id': field['id'],
				'label': field['label'],
				'value': self.data[field['id']]
			}
		return ret

	@property
	def tags(self):
		ret = {}
		for field in profile_schema['tags']:
			if field['id'] not in self.data:
				continue
			ret[field['id']] = {
				'id': field['id'],
				'label': field['label'],
				'values': self.data[field['id']].split(',')
			}
		return ret

	@property
	def links(self):
		ret = {}
		for field in profile_schema['links']:
			if field['id'] not in self.data:
				continue
			ret[field['id']] = {
				'id': field['id'],
				'label': field['label'],
				'prefix': field['prefix'],
				'value': self.data[field['id']]
			}
		return ret

def on_post_save(instance, **kwargs):
	if instance._password_set is not None:
		user = instance.associated_user
		if user is not None:
			user.set_password(instance._password_set)
			user.save()

post_save.connect(
	on_post_save,
	dispatch_uid = "maker_post_save",
	sender = Maker,
	weak = False,
)
