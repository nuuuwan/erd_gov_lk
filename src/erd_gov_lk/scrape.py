import os
from urllib import parse

from bs4 import BeautifulSoup
from utils import timex, tsv, www

from erd_gov_lk._constants import (DIR_DATA, DIR_GH_PAGES, DIR_ROOT,
                                   DONOR_LIST_FILE, PROJECT_LIST_FILE, URL_ERD,
                                   URL_INDEX_BILATERAL, URL_INDEX_MULTILATERAL)
from erd_gov_lk._utils import log
from erd_gov_lk.parse_helpers import parse_project


def init():
    os.system(f'rm -rf {DIR_ROOT}')
    os.system(f'mkdir {DIR_ROOT}')
    os.system(f'mkdir {DIR_DATA}')
    os.system(f'mkdir {DIR_GH_PAGES}')


def scrape_donor_list(donor_category, donor_url):
    html = www.read(donor_url)
    soup = BeautifulSoup(html, 'html.parser')
    donor_index = {}
    for option in soup.find_all('option'):
        donor_id = option.get('value')
        if donor_id:
            donor = {
                'donor_category': donor_category,
                'donor_id': (int)(donor_id),
                'donor_name': option.text,
            }
            donor_index[donor_id] = donor
    donor_list = sorted(donor_index.values(), key=lambda d: d['donor_id'])

    tsv.write(DONOR_LIST_FILE, donor_list)
    n_donor_list = len(donor_list)
    log.info(f'Wrote {n_donor_list} donors to {DONOR_LIST_FILE}')

    return donor_list


def get_url_donor(donor_id, sub_category_id, item_id):
    return URL_ERD + '?' + parse.urlencode({
        'option': 'com_rmobilization',
        'view': 'resource_project',
        'category_id': '1',
        'sub_category_id': sub_category_id,
        'searchby': 'donor_type',
        'donor_id': donor_id,
        'today': timex.get_date(),
        'Itemid': item_id,
        'lang': 'en',

    })


def scrape_donor(donor_category, donor_id, donor_name):
    if donor_category == 'bilateral':
        item_id, sub_category_id = '1', '321'
    else:
        item_id, sub_category_id = '2', '322'

    url = get_url_donor(donor_id, item_id, sub_category_id)
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
            'donor_category': donor_category,
            'donor_id': donor_id,
            'donor_name': donor_name,
            'source_url': url,
        } | parse_project(donor_id, donor_name, raw_project) | raw_project
        project_list.append(project)

    n_project_list = len(project_list)
    log.info(f'Found {n_project_list} projects for {donor_id} ({donor_name})')
    return project_list


def run():
    init()
    all_project_list = []

    for donor_category, donor_url in [
        ['bilateral', URL_INDEX_BILATERAL],
        ['multilateral', URL_INDEX_MULTILATERAL],
    ]:
        donor_list = scrape_donor_list(donor_category, donor_url)
        for d in donor_list:
            donor_id = d['donor_id']
            donor_name = d['donor_name']
            project_list = scrape_donor(donor_category, donor_id, donor_name)
            all_project_list += project_list

        all_project_list = sorted(
            all_project_list,
            key=lambda d: -d['amount_m_usd'],
        )

    n_all_project_list = len(all_project_list)
    log.info(f'Wrote {n_all_project_list} projects to {PROJECT_LIST_FILE}')
    tsv.write(PROJECT_LIST_FILE, all_project_list)


if __name__ == '__main__':
    run()
