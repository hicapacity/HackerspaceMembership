from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_password_reset(rn):
	email = rn.maker.email
	subject = "HiCap Password Reset"
	from_email = "passwordreset@hicapacity.mailgun.org"
	ctx = {
		'nonce': rn.nonce,
		'maker': rn.maker,
	}
	message = render_to_string("emails/password_reset.txt", ctx)
	send_mail(subject, message, from_email, [email,])
