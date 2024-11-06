from django.core.management.base import BaseCommand
from app.models import Operation, Ask, AskOperation, CustomUser

class Command(BaseCommand):
    help = 'Fills the database with test data: operations, users, asks, and ask-operation relationships'

    def handle(self, *args, **kwargs):
        # Создание пользователей
        for i in range(1, 11):
            email = f'user{i}@example.com'
            password = ''.join(str(x) for x in range(1, i+1)) 
            user, created = CustomUser.objects.get_or_create(
                email=email,
            )
            
            if created:
                user.set_password(password)  # Устанавливаем пароль, чтобы он был захеширован
                user.save()

                if i == 9 or i == 10:
                    user.is_staff = True
                    user.save()

                self.stdout.write(self.style.SUCCESS(f'User "{user.email}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.email}" already exists.'))

        # Добавляем вас как пользователя
        email = 'lans32@mail.ru'
        password = 'qwerty'
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={'password': password}
        )
        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User "{user.email}" created with password "{password}".'))
        else:
            self.stdout.write(self.style.WARNING(f'User "{user.email}" already exists.'))


        # Создание операторов
        operations_data = [
            {'id': 1, 'name': 'Дизъюнкция', 'operator_name': 'Оператор OR', 'photo': 'http://localhost:9000/bool/1.jpg', 'status': 'a', 'value_B': True, 'value_0': False, 'value_A': True, 'value_AB': True, 'description': 'возвращает истину, если хотя бы одно из значений истинно.'},
            {'id': 2, 'name': 'Конъюнкция', 'operator_name': 'Оператор AND', 'photo': 'http://127.0.0.1:9000/bool/2.gif', 'status': 'a', 'value_B': False, 'value_0': False, 'value_A': False, 'value_AB': True, 'description': 'возвращает истину только если оба значения истинны.'},
            {'id': 3, 'name': 'Исключающие "ИЛИ"', 'operator_name': 'Оператор XOR', 'photo': 'http://127.0.0.1:9000/bool/3.gif', 'status': 'a', 'value_B': True, 'value_0': False, 'value_A': True, 'value_AB': False, 'description': 'возвращает истину, если одно из значений истинно, но не оба.'},
            {'id': 4, 'name': 'Импликация', 'operator_name': 'Оператор IMPLIES', 'photo': 'http://127.0.0.1:9000/bool/4.gif', 'status': 'a', 'value_B': True, 'value_0': True, 'value_A': False, 'value_AB': True, 'description': 'возвращает ложь, только если первое значение истинно, а второе — ложно.'},
            {'id': 5, 'name': 'Эквиваленция', 'operator_name': 'Оператор XNOR', 'photo': 'http://127.0.0.1:9000/bool/5.gif', 'status': 'a', 'value_B': False, 'value_0': True, 'value_A': False, 'value_AB': True, 'description': 'возвращает истину, если оба значения равны (оба истинны или оба ложны).'},
            {'id': 6, 'name': 'Штрих Шеффера', 'operator_name': 'Оператор NAND', 'photo': 'http://127.0.0.1:9000/bool/6.gif', 'status': 'a', 'value_B': True, 'value_0': True, 'value_A': True, 'value_AB': False, 'description': 'возвращает ложь только если оба значения истинны.'},
            {'id': 9, 'name': 'Стрелка Пирса', 'operator_name': 'Оператор NOR', 'photo': 'http://localhost:9000/bool/7.gif', 'status': 'a', 'value_B': False, 'value_0': True, 'value_A': False, 'value_AB': False, 'description': 'возвращает истину, если оба значения ложны.'},
        ]

        for operation_data in operations_data:
            operation, created = Operation.objects.update_or_create(
                id=operation_data['id'],
                defaults={
                    'name': operation_data['name'],
                    'operator_name': operation_data['operator_name'],
                    'photo': operation_data['photo'],
                    'status': operation_data['status'],
                    'value_B': operation_data['value_B'],
                    'value_0': operation_data['value_0'],
                    'value_A': operation_data['value_A'],
                    'value_AB': operation_data['value_AB'],
                    'description': operation_data['description'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Operation "{operation.name}" added.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Operation "{operation.name}" updated.'))

        # Создание заявок
        asks_data = [
            {'id': 1, 'status': 'f', 'created_at': '2024-10-09 04:49:37.859275+00', 'formed_at': None, 'completed_at': '2024-10-21 20:12:32.65901+00', 'creator_id': 1, 'moderator_id': 2, 'first_operand': False},
            {'id': 2, 'status': 'f', 'created_at': '2024-10-09 04:49:37.860014+00', 'formed_at': '2024-10-15 22:24:22+00', 'completed_at': '2024-10-21 20:14:00.96605+00', 'creator_id': 2, 'moderator_id': 2, 'first_operand': False},
            {'id': 3, 'status': 'f', 'created_at': '2024-10-09 04:49:37.860507+00', 'formed_at': None, 'completed_at': '2024-10-21 20:13:23.782758+00', 'creator_id': 3, 'moderator_id': 2, 'first_operand': False},
            {'id': 4, 'status': 'dr', 'created_at': '2024-10-09 04:49:37.860997+00', 'formed_at': None, 'completed_at': None, 'creator_id': 4, 'moderator_id': None, 'first_operand': False},
            {'id': 5, 'status': 'dr', 'created_at': '2024-10-09 04:49:37.861474+00', 'formed_at': None, 'completed_at': None, 'creator_id': 5, 'moderator_id': None, 'first_operand': False},
        ]

        for ask_data in asks_data:
            ask, created = Ask.objects.update_or_create(
                id=ask_data['id'],
                defaults={
                    'status': ask_data['status'],
                    'created_at': ask_data['created_at'],
                    'formed_at': ask_data['formed_at'],
                    'completed_at': ask_data['completed_at'],
                    'creator_id': ask_data['creator_id'],
                    'moderator_id': ask_data.get('moderator_id'),
                    'first_operand': ask_data['first_operand'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Ask "{ask.id}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Ask "{ask.id}" updated.'))


        # Связывание операций и заявок через таблицу AskOperation
        ask_operation_data = [
            {'id': 1, 'ask_id': 1, 'operation_id': 1, 'second_operand': True, 'result': True},
            {'id': 2, 'ask_id': 2, 'operation_id': 2, 'second_operand': False, 'result': False},
            {'id': 3, 'ask_id': 2, 'operation_id': 3, 'second_operand': True, 'result': True},
            {'id': 4, 'ask_id': 3, 'operation_id': 1, 'second_operand': False, 'result': False},
            {'id': 5, 'ask_id': 3, 'operation_id': 2, 'second_operand': True, 'result': False},
            {'id': 6, 'ask_id': 3, 'operation_id': 3, 'second_operand': True, 'result': True},
        ]

        for ao_data in ask_operation_data:
            ask_operation, created = AskOperation.objects.update_or_create(
                id=ao_data['id'],
                defaults={
                    'ask_id': ao_data['ask_id'],
                    'operation_id': ao_data['operation_id'],
                    'second_operand': ao_data['second_operand'],
                    'result': ao_data['result'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'AskOperation entry {ao_data["id"]} created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'AskOperation entry {ao_data["id"]} updated.'))
