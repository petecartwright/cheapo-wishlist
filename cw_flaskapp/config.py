import os
import logging
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = 'YOUR SECRET KEY HERE'

MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


def get_logger(logger_name):
    current_date = datetime.now().strftime('%Y%m%d')
    current_folder = os.path.dirname(os.path.realpath(__file__))
    logfile = os.path.join(current_folder, 'app/log/refresh_log_{0}.txt'.format(current_date))

    logger = logging.getLogger(logger_name)

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger