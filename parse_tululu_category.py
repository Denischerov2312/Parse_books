import os
import json
import argparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from os.path import join
from urllib.parse import urlsplit

from parse_tululu import parse_book_page
from parse_tululu import download_book
from parse_tululu import get_response


def get_books_soup(url):
    response = get_response(url)
    soup = BeautifulSoup(response.content, 'lxml')
    selector = 'div[id^=content] table'
    return soup.select(selector)


def format_book_id(id):
    id = str(urlsplit(id).path)
    id = id.replace('/', '').replace('b', '')
    return id


def find_books_id(all_books):
    books_id = []
    for book in all_books:
        book_id = book.select_one('a')['href']
        book_id = format_book_id(book_id)
        books_id.append(book_id)
    return books_id


def download_book_json(book, folder='books_json/'):
    os.makedirs(folder, exist_ok=True)
    filename = f'{book["title"]}_json.json'
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'w', encoding='utf8') as file:
        json.dump(book, file, ensure_ascii=False)


def get_args():
    parser = argparse.ArgumentParser(description='Скачивает раздел жанр книг')
    parser.add_argument('--start_page', type=int,
                        help='Стартовая страница',
                        default=1)
    parser.add_argument('--end_page', type=int,
                        help='Конечная страница',
                        default=2)
    return parser.parse_args()


def main():
    args = get_args()
    for page in range(args.start_page, args.end_page):
        url = f'https://tululu.org/l55/{page}/'
        page_book_id = find_books_id(get_books_soup(url))
        for book_id in page_book_id:
            url = f'https://tululu.org/b{book_id}/'
            try:
                response = get_response(url)
            except requests.exceptions.HTTPError:
                print('Не существует такой книги')
                continue
            book = parse_book_page(response.text, response.url)
            filename = f"{book_id}.{book['title']}"
            image_url = book['image_url']
            download_book(filename, book_id, image_url)
            download_book_json(book)


if __name__ == '__main__':
    main()
