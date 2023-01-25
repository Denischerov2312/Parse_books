import os
import argparse
from os.path import split
from os.path import join
from urllib.parse import urljoin
from urllib.parse import unquote
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def parse_book_page(content):
    soup = BeautifulSoup(content, 'lxml')
    title = fing_title(soup)
    style = find_style(soup)
    comments = find_comments(soup)
    image_url = find_image_url(soup)
    book = {
        'title': title,
        'style': style,
        'comments': comments,
        'image_url': image_url,
    }
    return book


def find_comments(soup):
    texts = soup.find('div', id='content').find_all('div', class_='texts')
    comments = []
    for comment in texts:
        comments.append(comment.find('span').text)
    return comments


def find_style(soup):
    styles = soup.find('div', id='content').find('span', class_='d_book')
    styles = styles.find_all('a')
    all = []
    for style in styles:
        all.append(style.text)
    return all


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
    response.raise_for_status()
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'w', encoding='UTF-8') as file:
        file.write(response.text)
    return filepath


def download_image(url, folder='book_covers/'):
    if not url:
        return None
    response = requests.get(url)
    response.raise_for_status()
    path = urlsplit(url).path
    filename = unquote(split(path)[-1])
    os.makedirs(folder, exist_ok=True)
    filepath = join(folder, sanitize_filename(filename))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def get_args():
    parser = argparse.ArgumentParser(description='Скачивает книги')
    parser.add_argument('start_id', default=1, type=int, nargs='?')
    parser.add_argument('end_id', default=10, type=int, nargs='?')
    return parser.parse_args()


def main():
    args = get_args()
    for id in range(args.start_id, args.end_id):
        url = f'https://tululu.org/b{id}/'
        response = requests.get(url)
        try:
            check_for_redirect(response)
        except requests.HTTPError:
            print(f'Не существует такой ссылки - {url}')
            continue
        book = parse_book_page(response.text)
        filename = f"{id}.{book['title']}"
        text_url = f'https://tululu.org/txt.php?id={id}'
        download_txt(text_url, filename)
        download_image(book['image_url'])


if __name__ == '__main__':
    main()
