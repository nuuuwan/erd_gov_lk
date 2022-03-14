
from utils import timex

from erd_gov_lk._constants import CURRENCY_TO_TEXT_LIST, EXCHANGE_RATE_TO_USD


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
        return None, None, 0

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
