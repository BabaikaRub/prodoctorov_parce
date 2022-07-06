import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

import sys
import csv
import math
import os

from ui import Ui_MainWindow
from cities import city


# Класс парсера
class Parce(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_ui()
        self.ua = UserAgent()
        self.ui.comboBox.addItems(city.keys())
        self.ui.pushButton.clicked.connect(self.on_click)

    def init_ui(self):
        self.setWindowTitle('ПроДокторов')

    def on_click(self):
        self.collect_data(city[self.ui.comboBox.currentText()])

    def popup_end(self):
        msg = QMessageBox()
        msg.setWindowTitle('Информация')
        msg.setText('Файл успешно записан в папку "Результаты парсинга"')

        x = msg.exec_()

    def get_headers(self):
        headers = {
            'user-agent': self.ua.random,
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        return headers

    # Метод вычисления кол-ва страниц при пагинации
    def numbers_of_pages(self, city):
        address = f'https://prodoctorov.ru/{city}/lpu/?page=1'

        response = requests.get(url=address, headers=self.get_headers())
        soup = BeautifulSoup(response.text, 'lxml')

        total = soup.find('h1', class_='p-page__title')['data-counter']

        total = total.replace('(', '').replace(')', '').replace(' ', '')

        return math.ceil(int(total) / 20)

    def collect_data(self, city):
        # Создание файла с результатами парсинга
        if not os.path.isdir('Результаты парсинга'):
            os.mkdir('Результаты парсинга')

        with open(f'Результаты парсинга/{city}_res.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Наименование клиники', 'Направление', 'Номер телефона'])

        amount = self.numbers_of_pages(city)

        for page in range(1, amount + 1):
            # Отправка запроса на сайт
            response = requests.get(url=f'https://prodoctorov.ru/{city}/lpu/?page={page}', headers=self.get_headers())
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
                with open(f'Результаты парсинга/{city}_res.csv', 'a', encoding='utf-8-sig', newline='') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow([name, category, phone])

        self.popup_end()
        print('Файл записан')


def main():
    app = QtWidgets.QApplication([])
    application = Parce()
    application.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
