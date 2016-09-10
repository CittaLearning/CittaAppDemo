#!/usr/bin/env python
import os
import sys
from django.conf import settings
if __name__ == "__main__":
	sys.path.append('/Users/macbook/Desktop/CittaAppDemo/citta/')
	sys.path.append('/Users/macbook/Desktop/CittaAppDemo/citta/citta')
	os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
	if not settings.configured:
		settings.configure()
	from django.core.management import execute_from_command_line

	execute_from_command_line(sys.argv)
