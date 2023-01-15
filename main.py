import os
from os.path import split
from os.path import join
from urllib.parse import urljoin
from urllib.parse import unquote
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def get_book(id):
    response = requests.get(f'https://tululu.org/b{id}/')
    title = fing_title_of_book(response)
    image_url = find_image_url(response)
    text_url = f'https://tululu.org/txt.php?id={id}'
    return title, text_url, image_url


def download_txt(url, filename, folder='books/'):
    if not url:
        print('Не существует такой ссылки')
        return
    response = requests.get(url)
    response.raise_for_status()
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'w', encoding='UTF-8') as file:
        file.write(response.text)
    return filepath


def fing_title_of_book(response):
    try:
        check_for_redirect(response)
    except requests.HTTPError:
        return None
    soup = BeautifulSoup(response.text, 'lxml')
    heading = soup.find('h1').text
    title = heading.split('::')[0]
    return title.strip()


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_image(url, folder='book_covers/'):
    if not url:
        print('Не существует такой ссылки')
        return
    response = requests.get(url)
    response.raise_for_status()
    path = urlsplit(url).path
    filename = unquote(split(path)[-1])
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def find_image_url(response):
    try:
        check_for_redirect(response)
    except requests.HTTPError:
        return None
    soup = BeautifulSoup(response.text, 'lxml')
    url = soup.find('div', class_='bookimage').find('img')['src']
    return urljoin('https://tululu.org/', url)


def main():
    id = 0
    for _ in range(10):
        id += 1
        try:
            title, text_url, image_url = get_book(id)
        except requests.HTTPError:
            continue
        filename = f'{id}.{title}'
        download_txt(text_url, filename)
        download_image(image_url)


if __name__ == '__main__':
    main()
