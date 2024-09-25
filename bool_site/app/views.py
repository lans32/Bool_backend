from django.shortcuts import render
from test_data import OPERATIONS
from test_data import ASK_DATA

def index(request):
    operation_name = request.GET.get('operation')
    count_operations = 0
    for ask in ASK_DATA:
        count_operations += len(ask) - 2
    if operation_name:
        operations=[]
        for operation in OPERATIONS:
            if operation_name.lower() in operation['name'].lower():
                operations.append(operation)
        return render(request, 'index.html', {
            "operations": operations,
            'query': operation_name,
            "ask_id": 1,
            "count": count_operations
            })
    
    else:
        return render(request, 'index.html', {"operations": OPERATIONS, "ask_id": 1, "count": count_operations})

def operation(request, operation_id):
    for operator in OPERATIONS:
        if operator['id'] == operation_id:
            operation = operator
            break
    return render(request, 'operation.html', {"operation": operation})

def get_operation_by_id(operation_id):
    operation = next((operation for operation in OPERATIONS if operation['id'] == operation_id), None)
    if operation is None:
        raise ValueError(f"Operation with ID {operation_id} not found.")
    return operation

def ask(request, ask_id):
    # Поиск записи в базе данных по id
    ask_data = next((ask for ask in ASK_DATA if ask['id'] == ask_id), None)
    
    # Если запись найдена
    if ask_data:

        ask1_operation = get_operation_by_id(ask_data['ask1']['operation_id'])
        ask2_operation = get_operation_by_id(ask_data['ask2']['operation_id'])
        ask3_operation = get_operation_by_id(ask_data['ask3']['operation_id'])
        # Подготовка данных для контекста
        context = {
            'ask_id': ask_id,
            'first': ask_data['first'],
            'ask1': ask_data['ask1'],
            'ask1_operation': ask1_operation,
            'ask2': ask_data['ask2'],
            'ask2_operation': ask2_operation,
            'ask3': ask_data['ask3'],
            'ask3_operation': ask3_operation,
        }

        # Рендеринг страницы с контекстом
        return render(request, 'ask.html', context)

    # Если запись не найдена, возвращаем 404
    return render(request, '404.html')