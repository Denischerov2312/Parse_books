import os
import json
import argparse
import time

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from os.path import join
from urllib.parse import urlsplit

from parse_tululu import parse_book_page
from parse_tululu import download_book
from parse_tululu import get_response


def get_id(relative_path):
    relative_path = str(urlsplit(relative_path).path)
    book_id = relative_path.replace('/', '').replace('b', '')
    return book_id


def find_book_ids(all_books):
    book_ids = []
    for soup in all_books:
        relative_path = soup.select_one('a')['href']
        book_id = get_id(relative_path)
        book_ids.append(book_id)
    return book_ids


def save_books_json(books, dest_folder, folder='books_json/'):
    path = join(dest_folder, folder)
    os.makedirs(path, exist_ok=True)
    filename = f'{len(books)}books_json.json'
    filepath = join(path, sanitize_filename(filename))
    with open(filepath, 'w', encoding='utf8') as file:
        json.dump(books, file, ensure_ascii=False, indent=4)


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
    books = []
    for page_number in range(args.start_page, args.end_page):
        url = f'https://tululu.org/l55/{page_number}/'
        try:
            response = get_response(url)
        except requests.exceptions.HTTPError:
            print(f'Не существует такой страницы - {url}')
            continue
        soup = BeautifulSoup(response.content, 'lxml')
        selector = 'div[id^=content] table'
        page_book_ids = find_book_ids(soup.select(selector))
        for book_id in page_book_ids:
            url = f'https://tululu.org/b{book_id}/'
            try:
                response = get_response(url)
            except requests.exceptions.HTTPError:
                print(f'Не существует такой книги - {url}')
                continue
            book = parse_book_page(response.text, response.url)
            filename = f"{book_id}.{book['title']}"
            image_url = book['image_url']
            dest_folder = args.dest_folder
            while True:
                try:
                    book_path, img_path = download_book(filename, book_id, image_url,
                                                        dest_folder, args.skip_txt,
                                                        args.skip_imgs,
                                                        )
                    book['book_path'] = book_path
                    book['img_path'] = img_path
                    books.append(book)
                    break
                except requests.exceptions.ConnectionError:
                    print('Ошибка подключения')
                    time.sleep(5)
                except requests.exceptions.HTTPError:
                    print('Не существует такого url')
                    break

    save_books_json(books, dest_folder)


if __name__ == '__main__':
    main()
