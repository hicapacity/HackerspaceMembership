from django.db import models
from django.contrib.auth.models import User

class Maker(models.Model):
	user = models.OneToOneField(User)
	email = models.EmailField(unique=True)
	display_name = models.CharField(max_length=255)

	def __unicode__(self):
		return "{name} ({user})".format(name=self.display_name, user=self.user.username)

