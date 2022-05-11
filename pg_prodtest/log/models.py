from re import I
from django.db import models
from django.db.models import Index

class LogEntry(models.Model):
	body = models.JSONField(null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(null=True)

	@classmethod
	def count(cls):
		return cls.objects.count()

	class Meta:
		indexes = (
			models.Index(fields=['created', 'body'], name='super_log_entry_idx'),
		)