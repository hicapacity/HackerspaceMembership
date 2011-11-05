# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from hicap.membership.models import Maker
from hicap.billing.models import MembershipPayment, Donation
import datetime

def get_this_month():
	date = datetime.datetime.now()
	return date

class MemberView(object):
	@classmethod
	def frontpage(cls, request):
		context = {}
		return render_to_response("membership/frontpage.html", context, context_instance=RequestContext(request))

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

