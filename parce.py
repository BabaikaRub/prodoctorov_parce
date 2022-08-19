import traceback
import sys
import csv
import math
import os

import requests
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

from ui import Ui_MainWindow
from cities import city


# Класс приложения
class App(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_ui()
        self.ui.comboBox.addItems(city.keys())
        self.ui.pushButton.clicked.connect(self.start_parce)

    def init_ui(self):
        self.setWindowTitle('ПроДокторов')

    def start_parce(self):
        self.obj = Parce(city[self.ui.comboBox.currentText()])
        self.t = QThread()

        self.obj.moveToThread(self.t)
        self.t.started.connect(self.obj.start)
        self.obj.startSignal.connect(self.start_info)
        self.obj.updateSignal.connect(self.update_info)
        self.obj.finishSignal.connect(self.popup_end)

        self.t.start()

    def start_info(self):
        self.ui.label_3.setText('Парсинг начался! Ждите...')
        self.ui.pushButton.setEnabled(0)

    def update_info(self, info):
        self.ui.label_3.setText(f'Спаршено {info} строк информации!')

    def popup_end(self):
        msg = QMessageBox()
        msg.setWindowTitle('Информация')
        msg.setText('Файл успешно записан в папку "Результаты парсинга"')
        self.ui.label_3.setText('')
        self.ui.pushButton.setEnabled(1)

        x = msg.exec_()


# Класс парсера
class Parce(QObject):
    startSignal = pyqtSignal()
    updateSignal = pyqtSignal(int)
    finishSignal = pyqtSignal()

    def __init__(self, town):
        super().__init__()
        self.ua = UserAgent()
        self.town = town

    def start(self):
        self.collect_data()

        self.finishSignal.emit()

    def get_headers(self):
        headers = {
            'user-agent': self.ua.random,
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        return headers

    # Метод вычисления кол-ва страниц при пагинации
    def numbers_of_pages(self):
        address = f'https://prodoctorov.ru/{self.town}/lpu/?page=1'

        response = requests.get(url=address, headers=self.get_headers())
        soup = BeautifulSoup(response.text, 'lxml')

        total = soup.find('h1', class_='p-page__title')['data-counter']

        total = total.replace('(', '').replace(')', '').replace(' ', '')

        return math.ceil(int(total) / 20)

    def collect_data(self):

        self.startSignal.emit()

        # Создание файла с результатами парсинга
        if not os.path.isdir('Результаты парсинга'):
            os.mkdir('Результаты парсинга')

        with open(f'Результаты парсинга/{self.town}_res.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Наименование клиники', 'Направление', 'Номер телефона'])

        amount = self.numbers_of_pages()
        count = 0

        for page in range(1, amount + 1):
            # Отправка запроса на сайт
            response = requests.get(url=f'https://prodoctorov.ru/{self.town}/lpu/?page={page}', headers=self.get_headers())
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
                with open(f'Результаты парсинга/{self.town}_res.csv', 'a', encoding='utf-8-sig', newline='') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow([name, category, phone])

                if count >= 100 and count % 100 == 0:
                    self.updateSignal.emit(count)
                    count += 1
                else:
                    count += 1
                    continue


def main():

    def log_uncaught_exceptions(ex_cls, ex, tb):
        text = '{}: {}:\n'.format(ex_cls.__name__, ex)
        text += ''.join(traceback.format_tb(tb))

        print(text)
        QtWidgets.QMessageBox.critical(None, 'Error', text)
        quit()

    sys.excepthook = log_uncaught_exceptions

    app = QtWidgets.QApplication(sys.argv)
    application = App()
    application.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
