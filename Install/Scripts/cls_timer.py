# coding: utf-8

import time
import datetime


class Timer:
	def __init__(self):
		self.start_time = 0
		self.stop_time = 0
		self.last_time = 0

	def start(self):
		self.start_time = time.time()
		self.stop_time = 0
		self.last_time = 0

	def stop_lap(self, message):
		if self.last_time == 0:
			delta = time.time() - self.start_time
		else:
			delta = time.time() - self.last_time
		self.last_time = time.time()
		print u'{0} in {1}'.format(message, datetime.timedelta(seconds = delta))

	def stop(self, message = None):
		self.stop_time = time.time()
		if self.last_time == 0:
			delta = self.stop_time - self.start_time
		else:
			delta = self.stop_time - self.last_time
		overall = self.stop_time - self.start_time
		if message is not None:
			print u'{0} in {1}'.format(message, datetime.timedelta(seconds = delta))
		print u'Total time is {0}'.format(datetime.timedelta(seconds = overall))
