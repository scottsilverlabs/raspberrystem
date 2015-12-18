from bs4 import BeautifulSoup
import sys

def read_project_html(html_filename):
    with open(html_filename) as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Find last <div class=code>, and extract contents of <textarea> tag.
    code_divs = soup.find_all('div', attrs={'class': 'code'})
    code = code_divs[-1].textarea.contents[0]

    docstring = soup.find('div', id='description').contents[0]

    return docstring, code


try:
    docstring, code = read_project_html(sys.argv[1])
    print(code)
except IndexError:
    print("Usage: python3 scripts/mkproj.py PROJECT.html > /tmp/code.py", file=sys.stderr)
    print("Usually followed by:", file=sys.stderr)
    print("\t && scp /tmp/code.py pi@raspberrypi: && pi python3 code.py", file=sys.stderr)

