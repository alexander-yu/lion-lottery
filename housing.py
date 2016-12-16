from collections import namedtuple
import re
from StringIO import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser

import simplejson as json

from data import HOUSING_PDF

_REGEXES = {'pages': r'Page \d+ of \d+',
            'page': r'\n+',
            'uni': r'([a-zA-Z]+\d+|WITHHELD)',
            'priority': r'[1-3]\d\.\d{4}',
            'lottery_number': r'\d+'}
_SELECTION_TYPES = {'In-Person', 'Online'}
_MAX_GROUP_SIZE = 8

GroupID = namedtuple('GroupID', ['selection', 'priority', 'lottery_number'])


class Housing:
    def __init__(self, file_name):
        self.file_name = file_name
        self.groups = {}
        self.group_ids = {}
        self.groups_by_size = []
        self.groups_by_student = {}

    def _parse_data(file_name):
        data = ''
        housing_fb = open(file_name, 'rb')
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

    def _parse_page(self, page):
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
            group_id = GroupID(selections[i],
                               priorities[i],
                               lottery_numbers[i])
            self._add_student(uni, group_id)

    def _add_student(self, uni, group_id):
        self.groups_by_student[uni] = group_id

        if str(group_id) in self.groups:
            self.groups[str(group_id)].append(uni)

        else:
            self.groups[str(group_id)] = [uni]
            self.group_ids[str(group_id)] = group_id

        assert len(self.group_ids) == len(self.groups), \
            (self.group_ids, self.groups)

    def _split_groups_by_size(self):
        groups_by_size = [[] for _ in xrange(_MAX_GROUP_SIZE)]

        for group_id_str, group_id in self.group_ids.iteritems():
            group_size = len(self.groups[group_id_str])
            groups_by_size[group_size - 1].append(group_id)

        self.groups_by_size = groups_by_size

    def parse(self):
        pages = _parse_data(self.file_name)
        for page in pages:
            self._parse_page(page)

        self._split_groups_by_size()


if __name__ == "__main__":
    with open('./data/housing_data.json', 'w') as housing_json:
        housing_data = Housing(HOUSING_PDF)
        housing_data.parse()

        housing_dict = {
            "groups": housing_data.groups,
            "group_ids": housing_data.group_ids,
            "groups_by_size": housing_data.groups_by_size,
            "groups_by_student": housing_data.groups_by_student
        }

        housing_json.write(json.dumps(housing_dict, indent=4 * ' '))
