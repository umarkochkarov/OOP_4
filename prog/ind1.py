#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from datetime import datetime
import logging
import sys
from typing import List
import xml.etree.ElementTree as ET


# Класс пользовательского исключения в случае, если неверно
# введено время отправления.
class IllegalDateError(Exception):
    def __init__(self, time, message="Illegal date format"):
        self.date_str = time
        self.message = message
        super(IllegalDateError, self).__init__(message)

    def __str__(self):
        return f"{self.date_str} -> {self.message}"


# Класс пользовательского исключения в случае, если введенная
# команда является недопустимой.add
class UnknownCommandError(Exception):
    def __init__(self, command, message="Unknown command"):
        self.command = command
        self.message = message
        super(UnknownCommandError, self).__init__(message)

    def __str__(self):
        return f"{self.command} -> {self.message}"


@dataclass(frozen=True)
class Plane:
    name: str
    no: str
    time_str: str

    @property
    def time(self):
        # Преобразование строки времени в объект datetime при необходимости
        return datetime.strptime(self.time_str, "%H:%M").time()


@dataclass
class Planes:
    planes: List[Plane] = field(default_factory=lambda: [])

    def add(self, name, no, time):
        try:
            # Преобразовать введенную строку в объект datetime.time
            departure_time = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            raise IllegalDateError(time, "Неверный формат времени, используйте HH:MM")

        self.planes.append(
            Plane(name=name, no=no, time_str=time)  # Хранение времени как строки
        )

        self.planes.sort(key=lambda plane: plane.name)

    def __str__(self):
        # Заголовок таблицы.
        table = []
        line = "+-{}-+-{}-+-{}-+-{}-+".format("-" * 4, "-" * 25, "-" * 15, "-" * 20)
        table.append(line)
        table.append(
            "| {:^4} | {:^25} | {:^15} | {:^20} |".format(
                "№", "Пункт назначения", "Номер самолета", "Время отправления"
            )
        )
        table.append(line)

        # Вывести данные о всех самолетах.
        for idx, plane in enumerate(self.planes, 1):
            table.append(
                "| {:>4} | {:<25} | {:<15} | {:>20} |".format(
                    idx, plane.name, plane.no, plane.time_str
                )
            )

        table.append(line)

        return "\n".join(table)

    def select(self, nomer):
        result = []
        for plane in self.planes:
            if plane.no == str(nomer):
                result.append(plane)
        return result

    def load(self, filename):
        with open(filename, "r", encoding="utf8") as fin:
            xml = fin.read()

        parser = ET.XMLParser(encoding="utf8")
        tree = ET.fromstring(xml, parser=parser)

        self.planes = []
        for plane_element in tree:
            name, no, time_str = None, None, None

            for element in plane_element:
                if element.tag == "name":
                    name = element.text
                elif element.tag == "no":
                    no = element.text
                elif element.tag == "time":
                    time_str = element.text

                if name is not None and no is not None and time_str is not None:
                    self.planes.append(Plane(name=name, no=no, time_str=time_str))

    def save(self, filename):
        root = ET.Element("planes")
        for plane in self.planes:
            plane_element = ET.Element("plane")

            name_element = ET.SubElement(plane_element, "name")
            name_element.text = plane.name

            no_element = ET.SubElement(plane_element, "no")
            no_element.text = plane.no

            time_element = ET.SubElement(plane_element, "time")
            time_element.text = str(plane.time_str)

            root.append(plane_element)

        tree = ET.ElementTree(root)
        with open(filename, "wb") as fout:
            tree.write(fout, encoding="utf8", xml_declaration=True)


if __name__ == "__main__":
    # Выполнить настройку логгера.
    logging.basicConfig(filename="planes.log", level=logging.INFO)

    # Список самолетов.
    po = Planes()

    # Организовать бесконечный цикл запроса команд.
    while True:
        try:
            # Запросить команду из терминала.
            command = input(">>> ").lower()

            # Выполнить действие в соответствие с командой.
            if command == "exit":
                break

            elif command == "add":
                # Запросить данные о самолете.
                name = input("Пункт назначения? ")
                no = input("Номер самолета? ")
                time_str = input("Время отправления? ")

                # Добавить самолет.
                po.add(name, no, time_str)
                logging.info(
                    f"Добавлен самолет №{no}, пункт назначения: {name}, "
                    f"отправляющийся в {time_str}"
                )

            elif command == "list":
                # Вывести список.
                print(po)
                logging.info("Отображен список самолетов.")

            elif command.startswith("select "):
                # Разбить команду на части для выделения номера.
                parts = command.split(maxsplit=1)
                try:
                    nomer = parts[1]
                    # Запросить самолеты.
                    selected = po.select(nomer)
                    # Вывести результаты запроса.

                except ValueError:
                    print("Ошибка: Введите целое число для номера самолета")

                # Вывести результаты запроса.
                if selected:
                    for idx, plane in enumerate(selected, 1):
                        print("{:>4}: {}".format(idx, plane.name))
                    logging.info(
                        f"Найдено {len(selected)} самолетов " f"с номером {parts[1]}"
                    )

                else:
                    print("Самолеты с данным номером не найдены")
                    logging.warning(f"Самолеты с номером {parts[1]} не найдены.")

            elif command.startswith("load "):
                # Разбить команду на части для имени файла.
                parts = command.split(maxsplit=1)
                # Загрузить данные из файла.
                po.load(parts[1])
                logging.info(f"Загружены данные из файла {parts[1]}.")

            elif command.startswith("save "):
                # Разбить команду на части для имени файла.
                parts = command.split(maxsplit=1)
                # Сохранить данные в файл.
                po.save(parts[1])
                logging.info(f"Сохранены данные в файл {parts[1]}.")

            elif command == "help":
                # Вывести справку о работе с программой.
                print("Список команд:\n")
                print("add - добавить самолет;")
                print("list - вывести список самолетов;")
                print("select <номер> - запросить самолеты с номером;")
                print("load <имя_файла> - загрузить данные из файла;")
                print("save <имя_файла> - сохранить данные в файл;")
                print("help - отобразить справку;")
                print("exit - завершить работу с программой.")

            else:
                raise UnknownCommandError(command)

        except Exception as exc:
            logging.error(f"Ошибка: {exc}")
            print(exc, file=sys.stderr)
