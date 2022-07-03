import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import csv
import math


ua = UserAgent()

headers = {
    'user-agent': ua.random,
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Список городов
cities = ['moskva', 'spb', 'barnaul', 'vladivostok', 'volgograd', 'voronezh', 'ekaterinburg', 'izhevsk', 'kazan',
          'krasnodar', 'krasnoyarsk', 'nnovgorod', 'novosibirsk', 'omsk', 'perm', 'rostov-na-donu', 'samara', 'saratov',
          'tolyatti', 'ulyanovsk', 'ufa', 'chelyabinsk', 'yaroslavl']


# Функция вычисления кол-ва страниц при пагинации
def numbers_of_pages(city):
    address = f'https://prodoctorov.ru/{city}/lpu/?page=1'

    response = requests.get(url=address, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    total = soup.find('h1', class_='p-page__title')['data-counter']

    total = total.replace('(', '').replace(')', '').replace(' ', '')

    return math.ceil(int(total) / 20)


def collect_data(city):
    # Создание файла с результатами парсинга
    with open(f'{city}_res.csv', 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Наименование клиники', 'Направление', 'Номер телефона'])

    amount = numbers_of_pages(city)

    for page in range(1, amount + 1):
        # Отправка запроса на сайт
        response = requests.get(url=f'https://prodoctorov.ru/{city}/lpu/?page={page}', headers=headers)
        response.encoding = 'utf-8'

        # Парсинг отдельной страницы
        soup = BeautifulSoup(response.text, 'lxml')

        cards = soup.find('div', class_='appointments_page b-container').find_all('div', class_='b-card__top')

        for card in cards:

            name = card.find('a', class_='b-card__name-link b-link ui-text ui-text_h5 ui-text_color_primary-blue')\
                .text.strip()
            category = card.find('div', class_='b-card__category ui-text ui-text_body-1 ui-text_color_deep-grey')\
                .text.strip()

            try:
                phone = '+7 ' + card.find('span', {'class': 'b-card__lpu-phone-num'}).text
            except AttributeError:
                phone = 'Телефона нет'

            # Запись результатов парсинга
            with open(f'{city}_res.csv', 'a', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow([name, category, phone])

    print('Файл записан')


def main():
    collect_data('tolyatti')


if __name__ == '__main__':
    main()
