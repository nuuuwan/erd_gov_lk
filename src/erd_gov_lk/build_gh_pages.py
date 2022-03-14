import math
import os

import flag
from utils import tsv
from utils.xmlx import _, style

from erd_gov_lk._constants import DIR_ROOT, PROJECT_LIST_FILE, URL_ERD
from erd_gov_lk._utils import log


def get_projects():
    return tsv.read(PROJECT_LIST_FILE)


def render_project(x):
    i_project, project = x
    amount_m_usd = (float)(project['amount_m_usd'])
    if amount_m_usd == 0:
        return None
    font_size = max(12, math.sqrt(amount_m_usd * 2))
    dates = project['start_date'][:4]
    i1 = i_project + 1
    flag_str = flag.flag(project['country_code']) + \
        " " if project['country_code'] else ''
    return _('tr', [
        _('td', [
            _('div', f'#{i1}', {'class': 'div-row'})
        ]),

        _('td', [
            _(
                'div',
                f'{amount_m_usd:.0f}',
                {'class': 'div-amount'} | style(font_size=font_size),
            ),
            _('div', 'Million USD', {'class': 'div-unit'}),
        ]),

        _('td', [
            _('div', dates, {'class': 'div-date'}),
            _(
                'div',
                flag_str + project['donor_name'],
                {'class': 'div-donor'},
            ),
            _('a', [
                _('div', project['project_name'], {'class': 'div-project'})
            ], {'href': project['source_url']}),
            _('div', project['objectives'], {'class': 'div-objectives'}),
        ]),
    ])


def build():
    projects = get_projects()

    rendered_rows = list(map(
        render_project,
        enumerate(projects),
    ))

    table = _('table', [_('tbody', rendered_rows)])
    head = _('head', [
        _('link', None, {
            'rel': 'stylesheet',
            'href': 'styles.css',
        })
    ])
    body = _('body', [
        _('h3', 'Sri Lanka'),
        _('h1', 'Most Expensive Bilateral Loans'),
        _('p', [
            _('span', 'Source: '),
            _('a', 'Department of External Resources', {
                'href': URL_ERD,
            })
        ]),
        table,
    ])
    html = _('html', [head, body])
    html_file = os.path.join(DIR_ROOT, 'index.html')
    html.store(html_file)
    log.info(f'Wrote {html_file}')


def copy_files():
    os.system(f'cp src/erd_gov_lk/styles.css {DIR_ROOT}/')


if __name__ == '__main__':
    build()
    copy_files()
