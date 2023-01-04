import os

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def get_book(book_id):
    url = f'https://tululu.org/txt.php?id={book_id}'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    title = get_title_of_book(book_id)
    return title, response.text


def download_txt(filename, text, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, sanitize_filename(filename))
    with open(filepath, 'w', encoding='UTF-8') as file:
        file.write(text)
    return filepath


def get_title_of_book(id):
    url = f'https://tululu.org/b{id}/'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    heading = soup.find('h1').text
    title = heading.split('::')[0]
    return title.strip()


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.HTTPError


def main():
    id = 0
    for _ in range(10):
        id += 1
        try:
            title, text = get_book(id)
        except requests.HTTPError:
            continue
        print(download_txt(f'{id}.{title}.txt', text))


if __name__ == '__main__':
    main()
