# Create your views here.
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.sites.models import RequestSite

class MembersiteView(object):
	@classmethod
	def frontpage(cls, request):
		context = {
		}
		return render_to_response("page.html", context, context_instance = RequestContext(request))

