import requests


def get_book():
    url = 'https://tululu.org/txt.php?id=32168'
    response = requests.get(url)
    response.raise_for_status()
    
    with open('Пески Марса.txt', 'w', encoding='utf-8') as file:
        file.write(response.text)


if __name__ == '__main__':
    get_book()