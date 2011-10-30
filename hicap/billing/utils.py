import datetime
import calendar

def add_months(sourcedate, months):
	month = sourcedate.month - 1 + months
	year = sourcedate.year + month / 12
	month = month % 12 + 1
	day = min(sourcedate.day, calendar.monthrange(year, month)[1])
	if day < sourcedate.day:
		day = 1
		month += 1
		if month > 12:
			month = 1
			year += 1
	return datetime.date(year, month, day)

