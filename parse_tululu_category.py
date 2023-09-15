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


def get_books_soup():
    url = 'https://tululu.org/l55/'
    response = get_response(url)
    soup = BeautifulSoup(response.content, 'lxml')
    return soup.find('div', id='content').find_all('table')


def find_books_url(all_books):
    books_url = []
    for book in all_books:
        book_id = book.find('a')['href']
        book_url = urljoin('https://tululu.org/', book_id)
        books_url.append(book_url)
    return books_url


def main():
    url = 'https://tululu.org/l55/'
    response = get_response(url)
    soup = BeautifulSoup(response.content, 'lxml')
    book = soup.find('div', id='content').find('table').find('a')['href']
    print(urljoin('https://tululu.org/', book))


if __name__ == '__main__':
    print(find_books_url(get_books_soup()))
