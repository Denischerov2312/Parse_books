import os
import time
import argparse
from os.path import split
from os.path import join
from urllib.parse import urljoin
from urllib.parse import unquote
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def parse_book_page(content, response_url):
    soup = BeautifulSoup(content, 'lxml')
    title = fing_title(soup)
    genres = find_genres(soup)
    comments = find_comments(soup)
    image_url = find_image_url(soup, response_url)
    book = {
        'title': title,
        'genres': genres,
        'comments': comments,
        'image_url': image_url,
    }
    return book


def find_comments(soup):
    selector = 'div[id^=content] div.texts'
    texts = soup.select(selector)
    comments = [comment.find('span').text for comment in texts]
    return comments


def find_genres(soup):
    selector = 'div[id^=content] span.d_book a'
    content = soup.select(selector)
    genres = [genre.text for genre in content]
    return genres


def fing_title(soup):
    heading = soup.select_one('h1').text
    title = heading.split('::')[0]
    return title.strip()


def find_image_url(soup, response_url):
    selector = 'div.bookimage img'
    url = soup.select_one(selector)['src']
    return urljoin(response_url, url)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, id, filename, dest_folder, folder='books/'):
    id = id
    params = {'id': id}
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    path = join(dest_folder, folder)
    os.makedirs(path, exist_ok=True)
    filepath = join(path, sanitize_filename(filename))
    with open(filepath, 'w', encoding='UTF-8') as file:
        file.write(response.text)
    return filepath


def download_image(url, dest_folder, folder='book_covers/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    path = urlsplit(url).path
    filename = unquote(split(path)[-1])
    path = join(dest_folder, folder)
    os.makedirs(path, exist_ok=True)
    filepath = join(path, sanitize_filename(filename))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def add_args(parser):
    parser.add_argument('start_id', type=int, help='id, от которой скачаются книги')
    parser.add_argument('end_id', type=int, help='id, до которой скачаются книги')
    parser.add_argument('--dest_folder', type=str,
                        help='путь к каталогу с результатами парсинга',
                        default='parse_result/'
                        )
    parser.add_argument('--skip_txt', action='store_true',
                        help='При True не скачивает текст книги', default=False)
    parser.add_argument('--skip_imgs', action='store_true',
                        help='При True не скачивает обложки', default=False)
    return parser


def get_args(description):
    parser = argparse.ArgumentParser(description=description)
    add_args(parser)
    return parser.parse_args()


def download_book(filename, id, image_url, dest_folder, skip_txt=False, skip_imgs=False):
    while True:
        url = 'https://tululu.org/txt.php'
        try:
            if not skip_txt:
                download_txt(url, id, filename, dest_folder)
            if not skip_imgs:
                download_image(image_url, dest_folder)
            return
        except requests.exceptions.ConnectionError:
            print('Ошибка подключения')
            time.sleep(5)
        except requests.exceptions.HTTPError:
            print('Не существует такого url')
            return


def get_response(url):
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)
            break
        except requests.exceptions.ConnectionError:
            print('Ошибка подключения')
            time.sleep(5)
    return response


def main():
    args = get_args('Скачивает книги')
    for book_id in range(args.start_id, args.end_id):
        url = f'https://tululu.org/b{book_id}/'
        try:
            response = get_response(url)
        except requests.exceptions.HTTPError:
            print('Не существует такой ссылки')
            continue
        book = parse_book_page(response.text, response.url)
        filename = f"{book_id}.{book['title']}"
        image_url = book['image_url']
        download_book(filename, book_id, image_url,
                      args.dest_folder, args.skip_txt, args.skip_imgs)


if __name__ == '__main__':
    main()
