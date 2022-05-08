from django.http import HttpResponse
from django.urls import path
from django.views.generic import RedirectView

from .models import LogEntry

app_name = 'log'
urlpatterns = [
	path('', RedirectView.as_view(pattern_name='count')),
	path('count/', lambda request: HttpResponse(str(LogEntry.count())), name='count'),
]