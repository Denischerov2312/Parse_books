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


def download_book_json(book, dest_folder, folder='books_json/'):
    path = join(dest_folder, folder)
    os.makedirs(path, exist_ok=True)
    filename = f'{book["title"]}_json.json'
    filepath = join(path, sanitize_filename(filename))
    with open(filepath, 'w', encoding='utf8') as file:
        json.dump(book, file, ensure_ascii=False)


def get_args(description):
    parser = argparse.ArgumentParser(description)
    parser.add_argument('--start_page', type=int,
                        help='Стартовая страница',
                        default=1)
    parser.add_argument('--end_page', type=int,
                        help='Конечная страница',
                        default=2)
    parser.add_argument('--dest_folder', type=str,
                        help='путь к каталогу с результатами парсинга',
                        default='parse_result/'
                        )
    parser.add_argument('--skip_txt', action='store_true',
                        help='При True не скачивает текст книги', default=False)
    parser.add_argument('--skip_imgs', action='store_true',
                        help='При True не скачивает обложки', default=False)
    return parser.parse_args()


def main():
    args = get_args('Скачивает раздел жанр книг')
    for page_number in range(args.start_page, args.end_page):
        url = f'https://tululu.org/l55/{page_number}/'
        response = get_response(url)
        soup = BeautifulSoup(response.content, 'lxml')
        selector = 'div[id^=content] table'
        page_book_id = find_books_id(soup.select(selector))
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
            dest_folder = args.dest_folder
            download_book(filename, book_id, image_url, dest_folder, args.skip_txt, args.skip_imgs)
            download_book_json(book, dest_folder)


if __name__ == '__main__':
    main()
