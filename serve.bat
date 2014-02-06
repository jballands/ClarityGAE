@echo off
C:\Python27\python.exe "C:\Program Files (x86)\Google\google_appengine\dev_appserver.py" --skip_sdk_update_check=yes --host=0.0.0.0 --port=8000 --admin_host=0.0.0.0 --admin_port=8001 "%CD%"