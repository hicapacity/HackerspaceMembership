from django.db import models
from django.contrib.auth.models import User

class Maker(models.Model):
	user = models.OneToOneField(User)

	display_name = models.CharField(max_length=255)

