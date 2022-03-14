from urllib import parse

from bs4 import BeautifulSoup
from utils import timex, tsv, www

from erd_gov_lk._utils import log

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

DONOR_LIST_FILE = '/tmp/erd_gov_lk.donors.tsv'
PROJECT_LIST_FILE = '/tmp/erd_gov_lk.projects.tsv'

CURRENCY_TO_TEXT_LIST = {
    'EUR': ['Euro'],
    'GBP': [],
    'JPY': ['Yen'],
    'KWD': ['KD'],
    'USD': [],
}

EXCHANGE_RATE_TO_USD = {
    'EUR': 1.09,
    'GBP': 1.30,
    'JPY': 0.0085,
    'KWD': 3.29,
    'USD': 1,
}


def scrape_donor_list():
    html = www.read(URL_INDEX)
    soup = BeautifulSoup(html, 'html.parser')
    donor_index = {}
    for option in soup.find_all('option'):
        donor_id = option.get('value')
        if donor_id:
            donor = {
                'donor_id': (int)(donor_id),
                'donor_name': option.text,
            }
            donor_index[donor_id] = donor
    donor_list = sorted(donor_index.values(), key=lambda d: d['donor_id'])

    tsv.write(DONOR_LIST_FILE, donor_list)
    n_donor_list = len(donor_list)
    log.info(f'Wrote {n_donor_list} donors to {DONOR_LIST_FILE}')

    return donor_list


def parse_amount(raw_amount):
    amount = None
    currency = 'USD'
    amount_mult = 1
    for word in raw_amount.split(' '):
        for currency0, text_list in CURRENCY_TO_TEXT_LIST.items():
            for text in [currency0] + text_list:
                if text == word:
                    currency = currency0

        if word.lower() in ['mn', 'million', 'milion']:
            amount_mult = 1_000_000
        if word.lower() in ['billion']:
            amount_mult = 1_000_000_000

        if not amount:
            try:
                amount0 = (float)(word.replace(',', ''))
                amount = amount0
            except ValueError:
                pass

    if not amount:
        return None, None, None

    if amount < 1_000_000 and amount_mult == 1:
        amount_mult = 1_000_000
    amount_m = amount * amount_mult / 1_000_000
    amount_m_usd = amount_m * EXCHANGE_RATE_TO_USD[currency]
    return amount_m, currency, amount_m_usd


def parse_date(raw_date):
    if not raw_date:
        return None, None

    ut = None
    try:
        ut = timex.parse_time(raw_date, '%Y-%m-%d')
    except ValueError:
        pass
    return raw_date, ut


def parse_duration(raw_duration):
    duration = None
    duration_unit = None
    duration_unit_ticks = None
    duration_s = None
    if raw_duration:
        for word in raw_duration.split(' '):
            try:
                duration0 = (float)(word.replace(',', ''))
                duration = duration0
            except ValueError:
                pass

            if 'year' in word.lower():
                duration_unit = 'year'
                duration_unit_ticks = timex.SECONDS_IN.YEAR

    if duration and duration_unit_ticks:
        duration_s = duration * duration_unit_ticks
    return duration, duration_unit, duration_s


def parse_project(raw_project):
    amount, currency, amount_m_usd = parse_amount(raw_project['Amount (USD)'])
    start_date, start_ut = parse_date(raw_project['Commencement Date'])
    end_date, end_ut = parse_date(raw_project.get('Completed On'))

    duration, duration_unit, duration_unit_ticks = parse_duration(
        raw_project.get('Duration'))

    return {
        'project_name': raw_project['Project Name'],
        'is_loan': raw_project['Loan / Grant'].lower() == 'loan',
        'amount_m': amount,
        'currency': currency,
        'amount_m_usd': amount_m_usd,
        'objectives': raw_project['Objective/s'],
        'main_components': raw_project['Main Component/s'],
        'start_date': start_date,
        'start_ut': start_ut,
        'end_date': end_date,
        'end_ut': end_ut,
        'duration': duration,
        'duration_unit': duration_unit,
        'duration_unit_ticks': duration_unit_ticks,
        'implementing_agency': raw_project['Implementing Agency'],
        'executing_agency': raw_project['Executing Agency'],
    }


def get_donor_file(donor_id, ext):
    return f'/tmp/erd_gov_lk.donor.{donor_id}.{ext}'


def get_url_donor(donor_id):
    return URL_ERD + '?' + parse.urlencode({
        'option': 'com_rmobilization',
        'view': 'resource_project',
        'category_id': '1',
        'sub_category_id': '1',
        'searchby': 'donor_type',
        'donor_id': donor_id,
        'today': timex.get_date(),
        'Itemid': '321',
        'lang': 'en',

    })


def scrape_donor(donor_id, donor_name):
    url = get_url_donor(donor_id)
    html = www.read(url)
    soup = BeautifulSoup(html, 'html.parser')

    project_list = []
    for div_project in soup.find_all('div', {'class': 'panel-body'}):
        raw_project = {}
        for div_form_group in div_project.find_all(
                'div', {'class': 'form-group'}):
            labels = list(map(
                lambda x: x.text.strip(),
                div_form_group.find_all('label'),
            ))
            if len(labels) == 2:
                key_label, value_label = labels
                raw_project[key_label] = value_label
            elif len(labels) == 1:
                key_label = labels[0]
                value = list(map(
                    lambda li: li.text.strip(),
                    div_form_group.find_all('li'),
                ))
                raw_project[key_label] = '; '.join(value)

        project = {
            'donor_id': donor_id,
            'donor_name': donor_name,
            'source_url': url,
        } | parse_project(raw_project) | raw_project
        project_list.append(project)

    n_project_list = len(project_list)
    if n_project_list > 0:
        project_file = get_donor_file(donor_id, 'projects.tsv')
        tsv.write(project_file, project_list)
        log.info(f'Wrote {n_project_list} projects to {project_file}')

    return project_list


def run():
    donor_list = scrape_donor_list()
    all_project_list = []
    for d in donor_list:
        donor_id = d['donor_id']
        donor_name = d['donor_name']
        project_list = scrape_donor(donor_id, donor_name)
        all_project_list += project_list

    n_all_project_list = len(all_project_list)
    log.info(f'Wrote {n_all_project_list} projects to {PROJECT_LIST_FILE}')
    tsv.write(PROJECT_LIST_FILE, all_project_list)


if __name__ == '__main__':
    run()
