from argparse import ArgumentParser
from typing import Any, List, Tuple

from django.apps import apps
from django.conf import settings
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test.runner import DiscoverRunner


class NoCreateDbTestRunner(DiscoverRunner):
	''' Прогонщик тестов, предназначенный для стесненных условий разработки.

	В некоторых случаях необходимо, чтобы тестовая база не отличалась по типу
	от базы с реальными данными, но при этом прав на создание БД на сервере
	у пользователя нет.

	Стандартный для Django сценарий прогона тестов подразумевает создание
	новой базы данных перед провердением тестов и её удаление после их
	окончания. Вместо этого мы используем имеющуюся основную базу данных и
	только создаем и удаляем в ней тестовые таблицы, отличающиеся от
	основных таблиц префиксом.

	Опция ``--keepdb`` действует схожим для стандартного сценария обарзом, но
	распространяется только на таблицы, а не на базу. Если опция включена,
	после тестов таблицы удалены не будут.

	Если перед началом тестов тестовые таблицы уже есть в базе, то они будут
	удалены и пересозданы заново.

	Префикс можно задать либо через настройки с помощью
	переменной ``TEST_RUNNER_NOCREATEDB_TABLE_PREFIX``,
	либо через опцию ``--table-prefix``.

	Внутри тестов текущий табличный префикс можно узнать из настроек
	``settings.TEST_RUNNER_NOCREATEDB_TABLE_PREFIX``.
	'''

	DEFAULT_TABLE_PREFIX = 'test_'
	TABLE_PREFIX_SETTINGS_NAME = 'TEST_RUNNER_NOCREATEDB_TABLE_PREFIX'

	def __init__(self, *args, table_prefix=None, **kwargs):
		self.table_prefix = table_prefix
		self.keep_test_tables = kwargs['keepdb']
		self.default_db_connection = connections['default']  # TODO: Обобщить для любых баз
		kwargs['keepdb'] = True
		super().__init__(*args, **kwargs)

	@classmethod
	def add_arguments(cls, parser: ArgumentParser) -> None:
		# NOTE: В прогонщиках тестов этот метод вызывается перед
		# инициализатором __init__(), а все опции командной строки передаются
		# инициализатору в виде именнованных аргументов. Затем последовательно
		# вызываются ``setup_test_environment``, ``setup_databases``,
		# прогоняются все тесты, и далее ``teardown_databases`` и
		# ``teardown_test_environment``. См. также
		# https://docs.djangoproject.com/en/dev/topics/testing/advanced/#using-different-testing-frameworks
		super().add_arguments(parser)
		parser.add_argument(
			"--table-prefix",
			help="The prefix for test db tables when db user has no CREATEDB permission",
		)

	def setup_databases(self, **kwargs: Any) -> List[Tuple[BaseDatabaseWrapper, str, bool]]:
		connection = self.default_db_connection
		prefix = self.table_prefix
		available_tables = connection.introspection.table_names()
		for appname in apps.all_models:
			for model in apps.all_models[appname].values():
				if prefix and not model._meta.db_table.startswith(prefix):
					model._meta.db_table = prefix + model._meta.db_table
		with connection.schema_editor() as schema_editor:
			for model in apps.get_models():
				if model._meta.db_table in available_tables:
					schema_editor.delete_model(model)
				schema_editor.create_model(model)
		return []

	def teardown_databases(self, old_config: List[Tuple[BaseDatabaseWrapper, str, bool]], **kwargs: Any) -> None:
		if not self.keep_test_tables:
			connection = self.default_db_connection
			with connection.schema_editor() as schema_editor:
				for model in apps.get_models():
					schema_editor.delete_model(model)
		prefix = self.table_prefix
		for model in apps.get_models():
			if prefix and model._meta.db_table.startswith(prefix):
				model._meta.db_table = model._meta.db_table[len(prefix):]

	def _setup_table_prefix(self):
		if not self.table_prefix:
			self.table_prefix = getattr(
				settings, self.TABLE_PREFIX_SETTINGS_NAME,
				self.DEFAULT_TABLE_PREFIX)
		if not self.table_prefix:
			self.table_prefix = self.DEFAULT_TABLE_PREFIX
		self.old_settings_table_prefix = getattr(
			settings, self.TABLE_PREFIX_SETTINGS_NAME, None)
		setattr(settings, self.TABLE_PREFIX_SETTINGS_NAME, self.table_prefix)

	def setup_test_environment(self, **kwargs):
		self._setup_table_prefix()
		super().setup_test_environment(**kwargs)

	def teardown_test_environment(self, **kwargs):
		if self.old_settings_table_prefix is not None:
			setattr(settings, self.TABLE_PREFIX_SETTINGS_NAME,
					self.old_settings_table_prefix)
		super().teardown_test_environment(**kwargs)