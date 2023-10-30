import time
import json
from urllib.parse import urljoin
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from parse_tululu import parse_book_page
from parse_tululu import download_book


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


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def get_books_soup(url):
    response = get_response(url)
    soup = BeautifulSoup(response.content, 'lxml')
    return soup.find('div', id='content').find_all('table')


def find_books_urls(all_books):
    books_url = []
    for book in all_books:
        book_id = book.find('a')['href']
        book_url = urljoin('https://tululu.org/', book_id)
        books_url.append(book_url)
    return books_url


def main():
    url = 'https://tululu.org/l55/1/'
    response = get_response(url)
    soup = BeautifulSoup(response.content, 'lxml')
    book = soup.find('div', id='content').find('table').find('a')['href']
    print(urljoin('https://tululu.org/', book))


def get_book1(book_url):
    try:
        response = get_response(book_url)
    except requests.exceptions.HTTPError:
        print(f'Не существует такой ссылки - {book_url}')
        return False
    book = parse_book_page(response.text, response.url)
    filename = f"{book_id}.{book['title']}"
    image_url = book['image_url']
    download_book(filename, book_id, image_url)


if __name__ == '__main__':
    for page in range(1, 2):
        url = f'https://tululu.org/l55/{page}/'
        page_book_urls = find_books_urls(get_books_soup(url))
        for book_url in page_book_urls:
            book_id = str(urlsplit(book_url).path).replace('/', '').replace('b', '')
            try:
                response = get_response(book_url)
            except requests.exceptions.HTTPError:
                print(f'Не существует такой ссылки - {book_url}')
                continue
            book = parse_book_page(response.text, response.url)
            filename = f"{book_id}.{book['title']}"
            image_url = book['image_url']
            download_book(filename, book_id, image_url)
            book_json = json.dumps(book)
            with open(f'json_books/{book["title"]}json.json', 'w') as json_file:
                json_file.write(book_json)
