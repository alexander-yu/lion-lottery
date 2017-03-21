import cPickle as pickle
import os
import re

from collections import namedtuple
from StringIO import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser

import data
HOUSING_PDF = data.HOUSING_PDF
DATA_DIR = os.path.dirname(data.__file__) + '/'

IN_PERSON_SELECTION = 'In-Person'
ONLINE_SELECTION = 'Online'

REGEXES = {
    'pages': r'Page \d+ of \d+',
    'page': r'\n+',
    'uni': r'([a-zA-Z]+\d+|WITHHELD)',
    'priority': r'[1-3]\d\.\d{4}',
    'lottery_number': r'\d+'
}
SELECTION_TYPES = {IN_PERSON_SELECTION, ONLINE_SELECTION}
MAX_GROUP_SIZE = 8
PDF_CODEC = 'utf-8'
LAYOUT_ANALYSIS_PARAMS = LAParams()

Student = namedtuple('Student', ['uni', 'group_id'])


class GroupID(namedtuple('GroupID',
                         ['selection', 'priority', 'lottery_number'])):
    def __lt__(self, other):
        if self.selection == ONLINE_SELECTION and \
                other.selection == IN_PERSON_SELECTION:
            return False
        elif self.selection == IN_PERSON_SELECTION and \
                other.selection == ONLINE_SELECTION:
            return True

        if self.priority < other.priority:
            return False
        elif self.priority > other.priority:
            return True

        if self.lottery_number > other.lottery_number:
            return False
        elif self.lottery_number < other.lottery_number:
            return True

        return False


class Group:
    def __init__(self, group_id):
        self.group_id = group_id
        self.students = set()

    def __len__(self):
        return len(self.students)


class Housing:
    def __init__(self, file_name):
        self.groups = {}
        self.students = {}
        self.groups_by_size = []
        self._parse(file_name)

    @staticmethod
    def _parse_data(file_name):
        data = ''
        with open(file_name, 'rb') as housing_fb:
            housing_parser = PDFParser(housing_fb)
            housing_document = PDFDocument(housing_parser)

            if not housing_document.is_extractable:
                raise PDFTextExtractionNotAllowed

            resource_manager = PDFResourceManager()
            string_buffer = StringIO()
            device = TextConverter(resource_manager,
                                   string_buffer,
                                   codec=PDF_CODEC,
                                   laparams=LAYOUT_ANALYSIS_PARAMS)
            interpreter = PDFPageInterpreter(resource_manager, device)

            for page in PDFPage.create_pages(housing_document):
                interpreter.process_page(page)
                data = string_buffer.getvalue()

            return re.split(REGEXES['pages'], data)

    @staticmethod
    def _split_groups_by_size(groups):
        groups_by_size = [[] for _ in xrange(MAX_GROUP_SIZE)]

        for group_id in groups:
            group_size = len(groups[group_id])
            groups_by_size[group_size - 1].append(group_id)

        for group_list in groups_by_size:
            group_list.sort()

        return groups_by_size

    def _parse_page(self, page):
        unis = []
        selections = []
        priorities = []
        lottery_numbers = []

        for entry in re.split(REGEXES['page'], page):
            # first check if entry is a valid UNI
            if re.match(REGEXES['uni'], entry):
                unis.append(entry)
            # next check if entry is a valid selection type
            elif entry in SELECTION_TYPES:
                selections.append(entry)
            # next check if entry is a valid priority number
            elif re.match(REGEXES['priority'], entry):
                priorities.append(float(entry))
            # finally check if entry is valid lottery number
            # this check if performed only after the priority number
            # check; otherwise a priority number would match the regex
            elif re.match(REGEXES['lottery_number'], entry):
                lottery_numbers.append(int(entry))

        assert len(unis) == len(selections) \
            == len(priorities) == len(lottery_numbers), \
            (unis, selections, priorities, lottery_numbers)

        page_entries = len(unis)
        for i in xrange(page_entries):
            group_id = GroupID(selections[i],
                               priorities[i],
                               lottery_numbers[i])
            self._add_student(unis[i], group_id)

    def _add_student(self, uni, group_id):
        student = Student(uni, group_id)
        self.students[uni] = student

        if group_id not in self.groups:
            self.groups[group_id] = Group(group_id)

        self.groups[group_id].students.add(student)

    def _parse(self, file_name):
        pages = Housing._parse_data(file_name)
        for page in pages:
            self._parse_page(page)
        self.groups_by_size = Housing._split_groups_by_size(self.groups)


if __name__ == "__main__":
    with open(DATA_DIR + 'housing_data.pkl', 'wb') as housing_data_f:
        housing_data = Housing(HOUSING_PDF)
        pickle.dump(housing_data, housing_data_f, pickle.HIGHEST_PROTOCOL)
