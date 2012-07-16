# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from hicap.membership.models import Maker, ResetNonce
from hicap.membership.forms import MakerAuthForm, MakerProfileForm, PasswordChangeForm, PasswordResetForm, PasswordResetRequestForm, create_profile_form
from hicap.billing.models import MembershipPayment, Donation
from datetime import datetime, date, timedelta
from decimal import Decimal
import time

import json
from itertools import chain

def get_this_month():
	date = datetime.now()
	return date

def require_maker_login(func):
	def wrapped(cls, request):
		if not request.user.is_authenticated():
			return redirect("maker_login")
		if request.user.__class__ is not Maker:
			maker = Maker.objects.get(username=request.user.username)
		else:
			maker = request.user
		return func(cls, request, maker)
	return wrapped

class MemberView(object):
	@classmethod
	def frontpage(cls, request):
		auth_form = MakerAuthForm()
		context = {"auth_form": auth_form}
		return render_to_response("membership/frontpage.html", context, context_instance=RequestContext(request))

	@classmethod
	def login(cls, request):
		if request.method == "POST":
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				return redirect("maker_panel")
			auth_form = MakerAuthForm(request.POST)
		else:
			auth_form = MakerAuthForm()
		context = {"auth_form": auth_form}
		return render_to_response("membership/login.html", context, context_instance=RequestContext(request))

	@classmethod
	def logout(cls, request):
		logout(request)
		return redirect("maker_login")

	@classmethod
	@require_maker_login
	def panel(cls, request, maker):
		context = {
			'here': 'login',
			'maker': maker,
		}
		return render_to_response("membership/panel.html", context, context_instance=RequestContext(request))

	@classmethod
	@require_maker_login
	def info(cls, request, maker):
		if request.method == 'POST':
			form = MakerProfileForm(request.POST, instance = maker)
			error = True
			if form.is_valid():
				try:
					form.save()
					error = False
					msg = "Success"
				except Exception as e:
					msg = e.message
			else:
				msg = "Error Saving"
		else:
			form = MakerProfileForm(instance = maker)
			error = None
			msg = None
		context = {
			'here': 'info',
			'maker': maker,
			'form': form,
			'error': error,
			'msg': msg,
		}
		return render_to_response("membership/info.html", context, context_instance=RequestContext(request))

	@classmethod
	@require_maker_login
	def password(cls, request, maker):
		error = None
		msg = None
		if request.method == 'POST':
			error = True
			old_password = request.POST['old_password']
			new_password = request.POST['new_password']
			user = authenticate(username=maker.username, password=old_password)
			if user is not None:
				if len(new_password) > 0:
					maker.password = new_password
					maker.save()
					error = False
					msg = 'Password Changed'
				else:
					msg = 'No new password. LoL'
			else:
				msg = 'Your password is wrong. LoL'
		form = PasswordChangeForm()
		context = {
			'here': 'password',
			'maker': maker,
			'form': form,
			'error': error,
			'msg': msg,
		}
		return render_to_response("membership/password.html", context, context_instance=RequestContext(request))

	@classmethod
	def password_reset_request(cls, request):
		error = None
		msg = None

		if request.method == 'GET':
			form = PasswordResetRequestForm()

		if request.method == 'POST':
			username = request.POST['username']
			if len(username) > 0:
				try:
					maker = Maker.objects.get(username=username)
				except Maker.DoesNotExist:
					pass
				maker.send_password_reset()
				error = False
				msg = "Check your email"
			else:
				error = True
				msg = "Empty fields yo"
			form = PasswordResetRequestForm()

		context = {
			'here': 'password',
			'form': form,
			'error': error,
			'msg': msg,
		}
		return render_to_response("membership/password_reset_request.html", context, context_instance=RequestContext(request))

	@classmethod
	def password_reset(cls, request):
		error = None
		msg = None

		if request.method == 'GET':
			n = request.GET.get('n', None)
			form = PasswordResetForm(initial={'nonce':n})

		if request.method == 'POST':
			username = request.POST['username']
			nonce = request.POST['nonce']
			new_password = request.POST['new_password']
			error = True
			form = PasswordResetForm(request.POST)
			if len(new_password) > 0:
				try:
					maker = Maker.objects.get(username=username)
					hour_ago = datetime.now() - timedelta(hours=1)
					rn = ResetNonce.objects.filter(maker=maker, created__gte=hour_ago, nonce=nonce)
					if len(rn):
						error = False
						msg = "Success"
						maker.password = new_password
						maker.save()
						user = authenticate(username=maker.username, password=new_password)
						login(request, user)
						form = None
					else:
						msg = "Either username or nonce is wrong/expired"
				except Maker.DoesNotExist:
					msg = "Either username or nonce is wrong/expired"
					pass
			else:
				msg = "Empty fields yo"

		context = {
			'here': 'password_reset',
			'form': form,
			'error': error,
			'msg': msg,
		}
		return render_to_response("membership/password_reset.html", context, context_instance=RequestContext(request))

	@classmethod
	@require_maker_login
	def billing(cls, request, maker):
		history = maker.membershippayment_set.all()
		context = {
			'here': 'billing',
			'maker': maker,
			'history': history,
		}
		return render_to_response("membership/billing.html", context, context_instance=RequestContext(request))

	@classmethod
	@require_maker_login
	def community(cls, request, maker):
		_makers = Maker.objects.filter(publish_membership=True).select_related()
		makers = [m for m in _makers if m.is_current()]
		context = {
			'here': 'community',
			'maker': maker,
			'makers': makers,
		}
		return render_to_response("membership/community.html", context, context_instance=RequestContext(request))

	@classmethod
	@require_maker_login
	def profile(cls, request, maker):
		meta = maker.profile_data
		InfoForm, LinksForm, TagsForm = create_profile_form()
		if request.method == 'POST':
			infoForm = InfoForm(request.POST)
			linksForm = LinksForm(request.POST)
			tagsForm = TagsForm(request.POST)
			for field in chain(infoForm, linksForm, tagsForm):
				meta.update(field.name, field.value())
		else:
			infoForm = InfoForm(meta.data)
			linksForm = LinksForm(meta.data)
			tagsForm = TagsForm(meta.data)
		context = {
			'here': 'profile',
			'maker': maker,
			'meta': meta.data,
			'info_form': infoForm,
			'links_form': linksForm,
			'tags_form': tagsForm,
		}
		return render_to_response("membership/profile.html", context, context_instance=RequestContext(request))

	@classmethod
	@require_maker_login
	def preview(cls, request, maker):
		if not maker.is_current():
			reasons = ['Your profile isn\'t current',]
			context = {
				'here': 'preview',
				'maker': maker,
				'reasons': reasons
			}
			return render_to_response("membership/no_preview.html", context, context_instance=RequestContext(request))
		meta = maker.profile_data
		context = {
			'here': 'preview',
			'maker': maker,
			'info': meta.info,
			'links': meta.links,
			'tags': meta.tags,
		}
		return render_to_response("membership/preview.html", context, context_instance=RequestContext(request))



@staff_member_required
def admin_member_report(request, report_date=None):
	if report_date is None:
		report_date = datetime.now()

	month_start = date(report_date.year, report_date.month, 1)
	if report_date.month >= 12:
		month_end = date(report_date.year+1, 1, 1)
	else:
		month_end = date(report_date.year, report_date.month+1, 1)

	active_members = Maker.active_members(report_date)
	makers = Maker.objects.all()
	total_month_dues = MembershipPayment.monthly_sum(month_start, month_end)
	total_month_donations = Donation.monthly_sum(month_start, month_end)
	context = {
			'report_date': report_date,
			'title': "Report ({date})".format(date = report_date.strftime("%b %d, %Y")),
			'active_members': active_members,
			'total_in_system': len(makers),
			'total_month_dues': total_month_dues,
			'total_month_donations': total_month_donations,
	}
	return render_to_response("admin/membership/report.html", context, context_instance=RequestContext(request))

class CustomEncoder(json.JSONEncoder):
	def default(self, obj):
		try:
			return json.JSONEncoder.default(self, obj)
		except TypeError:
			try:
				return obj.forJSON
			except AttributeError:
				if isinstance(obj, Decimal):
					return float(obj)

@staff_member_required
def admin_member_report_ajax(request, report_date=None):
	makers = list(Maker.objects.all())
	context = {
			'makers': makers,
	}
	return HttpResponse(json.dumps(context, cls=CustomEncoder), mimetype="application/json")

@staff_member_required
def admin_payment_report_ajax(request, report_date=None):
	if report_date is None:
		report_date = datetime.now()

	month_start = date(report_date.year, report_date.month, 1)
	if report_date.month >= 12:
		month_end = date(report_date.year+1, 1, 1)
	else:
		month_end = date(report_date.year, report_date.month+1, 1)

	total_month_dues = MembershipPayment.monthly_sum(month_start, month_end)
	total_month_donations = Donation.monthly_sum(month_start, month_end)

	active_members = Maker.active_members(report_date)
	makers = Maker.objects.all()
	payments = list(MembershipPayment.objects.all())
	donations = list(Donation.objects.all())

	context = {
			'report_date': int(time.mktime(report_date.timetuple())),
			'title': "Report ({date})".format(date = report_date.strftime("%b %d, %Y")),
			'active_members': active_members,
			'total_in_system': len(makers),
			'total_month_dues': total_month_dues,
			'total_month_donations': total_month_donations,
			'payments': payments,
			'donations': donations,
	}
	return HttpResponse(json.dumps(context, cls=CustomEncoder), mimetype="application/json")
