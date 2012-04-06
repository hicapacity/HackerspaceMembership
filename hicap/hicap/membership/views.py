# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from hicap.membership.models import Maker
from hicap.membership.forms import MakerAuthForm
from hicap.billing.models import MembershipPayment, Donation
import datetime

def get_this_month():
	date = datetime.datetime.now()
	return date

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
	def panel(cls, request):
		if not request.user.is_authenticated():
			#return HttpResponseRedirect('/login/?next=%s' % request.path)
			return redirect("maker_login")
		context = {}
		return render_to_response("membership/panel.html", context, context_instance=RequestContext(request))

@staff_member_required
def admin_member_report(request, report_date=None):
	if report_date is None:
		report_date = datetime.datetime.now()

	month_start = datetime.date(report_date.year, report_date.month, 1)
	if report_date.month >= 12:
		month_end = datetime.date(report_date.year+1, 1, 1)
	else:
		month_end = datetime.date(report_date.year, report_date.month+1, 1)

	active_members = Maker.active_members(report_date)
	makers = Maker.objects.all()
	total_month_dues = MembershipPayment.monthly_sum(month_start, month_end)
	total_month_donations = Donation.monthly_sum(month_start, month_end)
	context = {
			'report_date': report_date,
			'title': "Report ({date})".format(date = report_date.strftime("%b %d, %Y")),
			'makers': makers,
			'active_members': active_members,
			'total_in_system': len(makers),
			'total_month_dues': total_month_dues,
			'total_month_donations': total_month_donations,
	}
	return render_to_response("admin/membership/report.html", context, context_instance=RequestContext(request))

