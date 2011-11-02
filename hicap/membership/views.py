# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required

class MemberView(object):
	@classmethod
	def frontpage(cls, request):
		context = {}
		return render_to_response("membership/frontpage.html", context, context_instance=RequestContext(request))

@staff_member_required
def admin_member_report(request):
	context = {}
	return render_to_response("admin/membership/report.html", context, context_instance=RequestContext(request))

