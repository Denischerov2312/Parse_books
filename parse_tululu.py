import os
import argparse
from os.path import split
from os.path import join
from urllib.parse import urljoin
from urllib.parse import unquote
from urllib.parse import urlsplit
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def parse_book_page(content):
    soup = BeautifulSoup(content, 'lxml')
    title = fing_title(soup)
    genre = find_genre(soup)
    comments = find_comments(soup)
    image_url = find_image_url(soup)
    book = {
        'title': title,
        'genre': genre,
        'comments': comments,
        'image_url': image_url,
    }
    return book


def find_comments(soup):
    texts = soup.find('div', id='content').find_all('div', class_='texts')
    comments = [comment.find('span').text for comment in texts]
    return comments


def find_genre(soup):
    content = soup.find('div', id='content').find('span', class_='d_book')
    content = content.find_all('a')
    genres = [genre.text for genre in content]
    return genres


def fing_title(soup):
    heading = soup.find('h1').text
    title = heading.split('::')[0]
    return title.strip()


def find_image_url(soup):
    url = soup.find('div', class_='bookimage').find('img')['src']
    return urljoin('https://tululu.org/', url)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, filename, folder='books/'):
    if not url:
        return None
    response = requests.get(url)
    try:
        response.raise_for_status()
        check_for_redirect(response)
    except requests.HTTPError:
        print(f'Не существует такой ссылки - {url}')
        return None
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'w', encoding='UTF-8') as file:
        file.write(response.text)
    return filepath


def download_image(url, folder='book_covers/'):
    if not url:
        return None
    response = requests.get(url)
    try:
        response.raise_for_status()
        check_for_redirect(response)
    except requests.HTTPError:
        print(f'Не существует такой ссылки - {url}')
        return None
    path = urlsplit(url).path
    filename = unquote(split(path)[-1])
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def get_args():
    parser = argparse.ArgumentParser(description='Скачивает книги')
    parser.add_argument('start_id', type=int)
    parser.add_argument('end_id', type=int)
    return parser.parse_args()


def main():
    args = get_args()
    for book_id in range(args.start_id, args.end_id):
        url = f'https://tululu.org/b{book_id}/'
        response = requests.get(url)
        try:
            response.raise_for_status()
            check_for_redirect(response)
        except requests.HTTPError:
            print(f'Не существует такой ссылки - {url}')
            continue
        book = parse_book_page(response.text)
        filename = f"{book_id}.{book['title']}"
        params = {'id': book_id}
        params = urlencode(params)
        text_url = f'https://tululu.org/txt.php?{params}'
        download_txt(text_url, filename)
        download_image(book['image_url'])


if __name__ == '__main__':
    main()
