import datetime

datetime_format = '%Y-%m-%d %H:%M:%S'
date_format = '%Y-%m-%d'

result = None
try:
    result = datetime.datetime.strptime('2014-2-28', date_format).date()
    result = datetime.datetime.strptime('2014-2-28', datetime_format)
except ValueError: pass

print(repr(result))