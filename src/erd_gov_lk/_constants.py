"""Constants."""
import os
from urllib import parse

CACHE_NAME = 'erd_gov_lk'
CACHE_TIMEOUT = 3600

DIR_ROOT = '/tmp/erd_gov_lk'
URL_ERD = 'http://www.erd.gov.lk/index.php'

URL_INDEX = URL_ERD + '?' + parse.urlencode({
    'option': 'com_rmobilization',
    'view': 'resource_project',
    'category_id': '1',
    'sub_category_id': '1',
    'searchby': 'donor_type',
    'Itemid': '321',
    'lang': 'en',
})

DONOR_LIST_FILE = os.path.join(DIR_ROOT, 'donors.tsv')
PROJECT_LIST_FILE = os.path.join(DIR_ROOT, 'projects.tsv')

CURRENCY_TO_TEXT_LIST = {
    'EUR': ['Euro'],
    'GBP': [],
    'JPY': ['Yen'],
    'KWD': ['KD'],
    'USD': ['US$'],
}

EXCHANGE_RATE_TO_USD = {
    'EUR': 1.09,
    'GBP': 1.30,
    'JPY': 0.0085,
    'KWD': 3.29,
    'USD': 1,
}
