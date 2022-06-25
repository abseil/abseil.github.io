r"""Add links to next page.

Usage:
$ python add_next_page.py --book_dir BOOK_DIR [options]
$ python add_next_page.py --help
"""

import os
from collections import OrderedDict
from urllib.parse import urldefrag

from absl import app, flags
from bs4 import BeautifulSoup

FLAGS = flags.FLAGS

flags.DEFINE_string('book_dir', None, 'Directory to HTML files of the book.')
flags.DEFINE_bool('rewrite_with_soup', False, 'Whether to rewrite HTML generated from Beautiful Soup.')


def main(_):
    with open(os.path.join(FLAGS.book_dir, 'toc.html')) as f:
        soup = BeautifulSoup(f, 'html5lib')

    chapters = OrderedDict()

    for a in soup.html.body.nav.ol.find_all('a'):
        url = urldefrag(a.get('href')).url
        if url not in chapters:
            chapters[a.get('href')] = a

    for file, link_to_next_page in zip(chapters.keys(), list(chapters.values())[1:]):
        link_to_next_page.string = 'Next: ' + link_to_next_page.string

        if FLAGS.rewrite_with_soup:
            with open(os.path.join(FLAGS.book_dir, file), 'r') as f:
                soup = BeautifulSoup(f, 'html5lib')

            if soup.html.body.contents[-1] != link_to_next_page:
                soup.html.body.append(link_to_next_page)

            with open(os.path.join(FLAGS.book_dir, file), 'w') as f:
                f.write(str(soup).replace("\N{NO-BREAK SPACE}", '&nbsp;'))

        else:
            with open(os.path.join(FLAGS.book_dir, file), 'r') as f:
                lines = f.readlines()

            assert lines[-2:] == ['  </body>\n', '</html>\n'], f'{lines[-3]}'

            if lines[-3] != str(link_to_next_page) + '\n':
                lines.insert(-2, str(link_to_next_page) + '\n')

            with open(os.path.join(FLAGS.book_dir, file), 'w') as f:
                f.writelines(lines)


if __name__ == '__main__':
    app.run(main)
