import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '_5#y2L"F4Q8z\n\*****xec]/'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Cm@3wzqf'
    MYSQL_DB = 'rctrophy38'
    MYSQL_CURSORCLASS = 'DictCursor'