from django.db import models

PAYMENT_TYPES = (
	('CC', 'Credit Card'),
	('PP', 'Paypal'),
	('CK', 'Check'),
)

# Create your models here.
class Payment(models.Model):
	maker = models.ForeignKey('membership.Maker')
	payment_created = models.DateTimeField(auto_now_add=True)
	cycle_start = models.DateField()
	norm_cycle_end = models.DateField()
	num_cycle = models.IntegerField()
	payment_amount = models.IntegerField(null=True)
	payment_type = models.CharField(max_length=32, choices=PAYMENT_TYPES)
	payment_note = models.TextField()

