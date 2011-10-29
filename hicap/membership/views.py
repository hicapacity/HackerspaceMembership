# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext

class MemberView(object):
	@classmethod
	def frontpage(cls, request):
		context = {}
		return render_to_response("membership/frontpage.html", context, context_instance=RequestContext(request))