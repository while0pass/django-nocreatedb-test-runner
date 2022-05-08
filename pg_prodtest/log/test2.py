from django.test import Client
from django.test import TestCase
from django.urls import reverse

from pg_prodtest.log.models import LogEntry


class Count3TestCase(TestCase):
	def test_count3(self):
		n = 7
		entries = [
			LogEntry(body={
				"test": True,
				"id": i + 11,
				"obj": { 'arr': [1, 'asdf', 2, 3] }
			})
			for i in range(n)
		]
		LogEntry.objects.bulk_create(entries)
		c = Client()
		response = c.get(reverse('log:count'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, bytes(str(n), encoding='utf-8'))


class Count4TestCase(TestCase):
	def test_count4(self):
		n = 7
		entries = [
			LogEntry(body={
				"test": True,
				"id": i + 11,
				"obj": { 'arr': [1, 'asdf', 2, 3] }
			})
			for i in range(n)
		]
		LogEntry.objects.bulk_create(entries)
		c = Client()
		response = c.get(reverse('log:count'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, bytes(str(n), encoding='utf-8'))