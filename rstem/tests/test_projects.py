'''
Tests of projects

Requires projects lid
'''
import testing_log
import testing
from functools import partial
from bs4 import BeautifulSoup

PRJ_PATH = '/opt/raspberrystem/projects/'

def read_project_html(html_filename_notext):
    with open(PRJ_PATH + html_filename_notext + '.html') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Find last <div class=code>, and extract contents of <textarea> tag.
    code_divs = soup.find_all('div', attrs={'class': 'code'})
    code = code_divs[-1].textarea.contents[0]

    docstring = soup.find('div', id='description').contents[0]

    return docstring, code

TESTS = [
    ('USING_BUTTONS_WITH_GPIO', '\nMore info...'),
    'FLASHLIGHT',
    'MANY_BUTTONS',
    'SOUNDS_-_SPEAKER',
    'MARY_HAD_A_LITTLE_LAMB',
    'SIMPLE_PIANO',
    'BETTER_PIANO',
    'SIMON_1',
    'SIMON_2',
    'SIMON_3',
    'SIMON_4',
    'SIMON_5',
    'SIMON_6',
    'SIMON_7',
    'LED_MATRIX',
    'GAME_LOOPS',
    'BOUNCING_BALL_1',
    'BOUNCING_BALL_2',
    'ACCELEROMETER',
    'SPACE_INVADERS_1',
    'SPACE_INVADERS_2',
    'SPACE_INVADERS_3',
    'SPACE_INVADERS_4',
    'SPACE_INVADERS_5',
    'SPACE_INVADERS_6',
    'SPACE_INVADERS_7',
    'SPACE_INVADERS_8',
    'SPACE_INVADERS_9',
]

def test_factory():
    for test_name in TESTS:
        # Support test_name being either the filename or a tuple of (filename,
        # additional_docstring)
        additional_docstring = ''
        if isinstance(test_name, tuple):
            test_name, additional_docstring = test_name

        docstring, code = read_project_html(test_name)

        new_test = partial(exec, code)
        new_test.__name__ = test_name
        new_test.__doc__ = docstring + additional_docstring
        new_test = testing.manual_io(new_test)
        globals()[test_name] = new_test

test_factory()
