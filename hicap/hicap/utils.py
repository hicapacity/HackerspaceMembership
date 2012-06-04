import time
import datetime

def to_unixtime(d):
	return int(time.mktime(d.timetuple()))
