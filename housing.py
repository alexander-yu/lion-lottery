import re
from StringIO import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser

from data import HOUSING_PDF

_REGEXES = {'pages': r'Page \d+ of \d+',
            'page': r'\n+',
            'uni': r'([a-zA-Z]+\d+|WITHHELD)',
            'priority': r'[1-3]\d\.\d{4}',
            'lottery_number': r'\d+'}
_SELECTION_TYPES = {'In-Person', 'Online'}
_MAX_GROUP_SIZE = 8


class Housing:
    def __init__(self):
        self.groups = {}
        self.students = {}
        self.group_ids = []
        self.groups_by_size = []


def _parse_data():
    data = ''
    housing_fb = open(HOUSING_PDF, 'rb')
    housing_parser = PDFParser(housing_fb)
    housing_document = PDFDocument(housing_parser)

    if not housing_document.is_extractable:
        raise PDFTextExtractionNotAllowed

    resource_manager = PDFResourceManager()
    string_buffer = StringIO()
    layout_analysis_params = LAParams()
    codec = 'utf-8'
    device = TextConverter(resource_manager, string_buffer, codec=codec,
                           laparams=layout_analysis_params)
    interpreter = PDFPageInterpreter(resource_manager, device)

    for page in PDFPage.create_pages(housing_document):
        interpreter.process_page(page)
        data = string_buffer.getvalue()

    housing_fb.close()
    return re.split(_REGEXES['pages'], data)


def _parse_page(page, housing_data):
    unis = []
    selections = []
    priorities = []
    lottery_numbers = []

    for entry in re.split(_REGEXES['page'], page):
        # first check if entry is a valid UNI
        if re.match(_REGEXES['uni'], entry):
            unis.append(entry)

        # next check if entry is a valid selection type
        elif entry in _SELECTION_TYPES:
            selections.append(entry)

        # next check if entry is a valid priority number
        elif re.match(_REGEXES['priority'], entry):
            priorities.append(entry)

        # finally check if entry is valid lottery number
        # this check if performed only after the priority number
        # check; otherwise a priority number would match the regex
        elif re.match(_REGEXES['lottery_number'], entry):
            lottery_numbers.append(entry)

    assert len(unis) == len(selections) \
        == len(priorities) == len(lottery_numbers), \
        (unis, selections, priorities, lottery_numbers)

    page_entries = len(unis)
    for i in xrange(page_entries):
        uni = unis[i]
        group_id = (selections[i], priorities[i], lottery_numbers[i])
        _add_student(uni, group_id, housing_data)


def _add_student(uni, group_id, housing_data):
    housing_data.students[uni] = group_id

    if group_id in housing_data.groups:
        housing_data.groups[group_id].append(uni)

    else:
        housing_data.groups[group_id] = [uni]
        housing_data.group_ids.append(group_id)

    assert len(housing_data.group_ids) == len(housing_data.groups), \
        (housing_data.group_ids, housing_data.groups)


def _split_groups_by_size(housing_data):
    groups_by_size = [[] for _ in xrange(_MAX_GROUP_SIZE)]

    for group_id in housing_data.group_ids:
        group_size = len(housing_data.groups[group_id])
        groups_by_size[group_size - 1].append(group_id)

    housing_data.groups_by_size = groups_by_size


def get_data():
    housing_data = Housing()
    pages = _parse_data()

    for page in pages:
        _parse_page(page, housing_data)

    _split_groups_by_size(housing_data)

    return housing_data
