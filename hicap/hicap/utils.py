import time
import datetime

def to_unixtime(d):
	return int(time.mktime(d.timetuple()))

class AttrDict(dict):
	def __getattr__(self, key):
		return self[key]

	def __setattr__(self, key, value):
		self[key] = value
