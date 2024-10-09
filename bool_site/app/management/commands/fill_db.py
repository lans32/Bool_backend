from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from app.models import Operation, Ask, AskOperation

class Command(BaseCommand):
    help = 'Fills the database with test data: operations, users, asks, and ask-operation relationships'

    def handle(self, *args, **kwargs):
        # Создание пользователей
        for i in range(1, 11):
            password = ''.join(str(x) for x in range(1, i + 1))
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={'last_login': timezone.now()}
            )
            if created:
                # Hash the password before saving
                user.set_password(password)
                user.save()

                # Assign users 9 and 10 as administrators
                if i == 9 or i == 10:
                    user.is_staff = True
                    user.save()

                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.username}" already exists.'))


        # Создание операторов
        operations_data = [
            {'name': 'Дизъюнкция', 'description': 'Оператор OR', 'photo': 'http://127.0.0.1:9000/bool/1.gif'},
            {'name': 'Конъюнкция', 'description': 'Оператор AND', 'photo': 'http://127.0.0.1:9000/bool/2.gif'},
            {'name': 'Исключающие "ИЛИ"', 'description': 'Оператор XOR', 'photo': 'http://127.0.0.1:9000/bool/3.gif'},
            {'name': 'Импликация', 'description': 'Оператор IMPLIES', 'photo': 'http://127.0.0.1:9000/bool/4.gif'},
            {'name': 'Эквиваленция', 'description': 'Оператор XNOR', 'photo': 'http://127.0.0.1:9000/bool/5.gif'},
            {'name': 'Штрих Шеффера', 'description': 'Оператор NAND', 'photo': 'http://127.0.0.1:9000/bool/6.gif'},
            {'name': 'Стрелка Пирса', 'description': 'Оператор NOR', 'photo': 'http://127.0.0.1:9000/bool/7.gif'},
        ]

        for operation_data in operations_data:
            operation, created = Operation.objects.get_or_create(
                name=operation_data['name'],
                defaults={
                    'description': operation_data['description'],
                    'photo': operation_data['photo'],
                    'status': 'a'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Operation "{operation.name}" added.'))
            else:
                self.stdout.write(self.style.WARNING(f'Operation "{operation.name}" already exists.'))

        # Создание заявок
        asks_data = [
            {'creator_id': 1},
            {'creator_id': 2},
            {'creator_id': 3},
            {'creator_id': 4},
            {'creator_id': 5},
        ]

        for ask_data in asks_data:
            ask, created = Ask.objects.get_or_create(
                creator_id=ask_data['creator_id'],
                defaults={
                    'status': 'dr',
                    'first_operand': False, 
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Ask "{Ask.ask_id}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Ask "{Ask.ask_id}" already exists.'))

        # Связывание операций и заявок через таблицу AskOperation
        ask_operation_data = [
            {'ask_id': 1, 'operation_id': 1, 'second_operand': True},
            {'ask_id': 2, 'operation_id': 2, 'second_operand': False},
            {'ask_id': 2, 'operation_id': 3, 'second_operand': True},
            {'ask_id': 3, 'operation_id': 1, 'second_operand': False},
            {'ask_id': 3, 'operation_id': 2, 'second_operand': True},
            {'ask_id': 3, 'operation_id': 3, 'second_operand': True},
            {'ask_id': 4, 'operation_id': 4, 'second_operand': False},
            {'ask_id': 5, 'operation_id': 1, 'second_operand': True},
            {'ask_id': 5, 'operation_id': 3, 'second_operand': False},
        ]

        for ao_data in ask_operation_data:
            ask_operation, created = AskOperation.objects.get_or_create(
                ask_id=ao_data['ask_id'],
                operation_id=ao_data['operation_id'],
                defaults={'second_operand': ao_data['second_operand']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'AskOperation entry for fight {ao_data["ask_id"]}, operation {ao_data["operation_id"]} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'AskOperation entry for fight {ao_data["ask_id"]}, operation {ao_data["operation_id"]} already exists.'))