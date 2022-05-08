from django.db import models

class LogEntry(models.Model):
	body = models.JSONField(null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(null=True)

	@classmethod
	def count(cls):
		return cls.objects.count()