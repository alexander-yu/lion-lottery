import re
from StringIO import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser

_REGEXES = {'pages': r'Page \d+ of \d+',
            'page': r'\n+',
            'uni': r'([a-z]+\d+|WITHHELD)',
            'priority': '[1-3]\d\.\d{4}',
            'lottery_number': '\d+'
            }
_HOUSING_PDF = 'AY_1617_Lottery_numbers_by_Priority.pdf'


def _parse_data():
    data = ''
    housing_parser = PDFParser(open(_HOUSING_PDF, 'rb'))
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

    return re.split(_REGEXES['pages'], data)


def _parse_page(page, groups, students, group_ids):
    unis = []
    selections = []
    priorities = []
    lottery_numbers = []

    for entry in re.split(_REGEXES['page'], page):
        # first check if entry is a valid UNI
        if re.match(_REGEXES['uni'], entry):
            unis.append(entry)

        # next check if entry is a valid selection type
        elif entry == 'In-Person' or entry == 'Online':
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
        == len(priorities) == len(lottery_numbers)

    page_entries = len(unis)
    for i in xrange(page_entries):
        uni = unis[i]
        group_id = (selections[i], priorities[i], lottery_numbers[i])

        students[uni] = group_id

        if group_id in groups:
            groups[group_id].append(uni)

        else:
            groups[group_id] = [uni]
            group_ids.append(group_id)

        assert len(group_ids) == len(groups)
