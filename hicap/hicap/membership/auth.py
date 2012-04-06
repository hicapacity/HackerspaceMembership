from hicap.membership.models import Maker

class MakerBackend(object):
	supports_object_permissions = False
	supports_anonymous_user = False
	supports_inactive_user = False
	def authenticate(self, username=None, password=None):
		try:
			user = Maker.objects.get(username=username)
			if user.check_password(password):
				return user
		except Maker.DoesNotExist:
			pass
		return None

	def get_user(self, user_id):
		try:
			return Maker.objects.get(pk=user_id)
		except Maker.DoesNotExist:
			pass
		return None
