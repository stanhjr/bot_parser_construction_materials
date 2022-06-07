from datetime import datetime, timedelta

from aiogram import types
from sqlalchemy import and_

from models.tabs import session, Employees


def is_number(string):
    try:
        string = string.replace(" ", "")
        string = string.replace(",", ".")
        return float(string)
    except ValueError:
        return False


class DataApi:
    def __init__(self):
        self.session = session

    def create_employee(self, message: types.Message):
        with self.session() as s:
            employee = s.query(Employees).filter(Employees.telegram_id == message.from_user.id).first()

            if not employee:
                employee = Employees(telegram_id=message.from_user.id,
                                     username=message.from_user.username,
                                     first_name=message.from_user.first_name,
                                     last_name=message.from_user.last_name)
                s.add(employee)
                s.commit()

            return True

    def delete_employee(self, employee_id):
        with self.session() as s:
            s.query(Employees).filter(Employees.id == employee_id).delete()
            s.commit()
            return True

    def get_employees_first_name(self):
        with self.session() as s:
            employees = s.query(Employees).all()
            result_list = []
            for employee in employees:
                tuple_employee = (employee.id, employee.first_name)
                result_list.append(tuple_employee)
            return result_list

    def get_employees_telegram_ids(self):
        with self.session() as s:

            return [x.telegram_id for x in s.query(Employees).all()]

    def update_product_list_employee(self, message: types.Message, list_groups_product: list):
        with self.session() as s:
            employee = s.query(Employees).filter(Employees.telegram_id == message.from_user.id).first()
            employee.set_list_groups_product(list_groups_product)
            s.add(employee)
            s.commit()

            return True

    def get_employees_product_lists(self):
        with self.session() as s:
            employees = s.query(Employees).all()
            result_list = []
            for employee in employees:
                tuple_employee = (employee.telegram_id, employee.get_list_groups_product)
                result_list.append(tuple_employee)
            return result_list

    def get_user_groups(self, user_telegram_id):
        with self.session() as s:
            user = s.query(Employees).filter(Employees.telegram_id == user_telegram_id).first()
            if user:
                return user.get_list_groups_product


data_api = DataApi()
