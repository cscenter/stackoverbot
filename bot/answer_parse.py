from bs4 import BeautifulSoup
import html2text


def prepare_for_markdown(message):
    message = message.replace('*', r'\*')
    message = message.replace('_', r'\_')
    soup = BeautifulSoup(message, "html.parser")
    for tag in soup.findAll():
         if tag.name == 'code':
             if tag.string is not None:
                  tag.string.replace_with(str(tag.string).replace('\*', '*'))
                  tag.string.replace_with(str(tag.string).replace('\_', '_'))
         elif tag.name == 'a':
             if tag['href'] is not None:
                 tag.replaceWith(tag['href'])
         elif tag.name == 'strong':
             if tag.string is not None:
                 tag.string = '*' + tag.string + '*'
    pretty_soup = soup.prettify()
    pretty_html = html2text.html2text(pretty_soup)
    h = pretty_html.replace('\n\n', '\n')
    h = bytes(h, "utf-8").decode("unicode_escape")
    return h
