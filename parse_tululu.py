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
    texts = soup.find('div', id='content').find_all('div', class_='texts')
    comments = [comment.find('span').text for comment in texts]
    return comments


def find_genres(soup):
    content = soup.find('div', id='content').find('span', class_='d_book')
    content = content.find_all('a')
    genres = [genre.text for genre in content]
    return genres


def fing_title(soup):
    heading = soup.find('h1').text
    title = heading.split('::')[0]
    return title.strip()


def find_image_url(soup, response_url):
    url = soup.find('div', class_='bookimage').find('img')['src']
    return urljoin(response_url, url)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, params, filename, folder='books/'):
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'w', encoding='UTF-8') as file:
        file.write(response.text)
    return filepath


def download_image(url, folder='book_covers/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    path = urlsplit(url).path
    filename = unquote(split(path)[-1])
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def get_args():
    parser = argparse.ArgumentParser(description='Скачивает книги')
    parser.add_argument('start_id', type=int, help='id, от которой скачаются книги')
    parser.add_argument('end_id', type=int, help='id, до которой скачаются книги')
    return parser.parse_args()


def download_book(filename, params, image_url):
    while True:
        url = 'https://tululu.org/txt.php'
        try:
            download_txt(url, params, filename)
            download_image(image_url)
            return
        except requests.exceptions.ConnectionError:
            print('Ошибка подключения')
            time.sleep(5)
        except requests.exceptions.HTTPError:
            print('Не существует такого url')
            return


def get(url):
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
    args = get_args()
    for book_id in range(args.start_id, args.end_id):
        url = f'https://tululu.org/b{book_id}/'
        try:
            response = get(url)
        except requests.exceptions.HTTPError:
            print(f'Не существует такой ссылки - {url}')
            continue
        book = parse_book_page(response.text, response.url)
        filename = f"{book_id}.{book['title']}"
        params = {'id': book_id}
        image_url = book['image_url']
        download_book(filename, params, image_url)


if __name__ == '__main__':
    main()
