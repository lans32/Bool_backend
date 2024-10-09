from django.shortcuts import render, get_object_or_404, redirect
from .models import Operation, Ask, AskOperation
from django.db import connection

def add_operation_to_ask(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    user = request.user

    try:
        ask = Ask.objects.get(creator=user, status='dr')
    except Ask.DoesNotExist:
        ask = Ask.objects.create(creator=user, status='dr')

    ask_operation, created = AskOperation.objects.get_or_create(ask=ask, operation=operation)
    ask_operation.save()

    return redirect('index')

def delete_ask(request, ask_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_ask SET status = 'del' WHERE id = %s", [ask_id])
    
    return redirect('index')

def index(request):
    user = request.user
    operation_name = request.GET.get('operation')
    first_ask = Ask.objects.first()
    count_operations = AskOperation.objects.filter(ask=first_ask).count() if first_ask else 0
    curr_ask = Ask.objects.filter(creator=user, status='dr').first()
    if curr_ask:
        ask_info = {
            'id': curr_ask.id,
            'count': Ask.objects.get_total_operations(curr_ask)
        }
    else:
        ask_info = None

    if operation_name:
        operations = Operation.objects.filter(name__icontains=operation_name)
        return render(request, 'index.html', {
            "operations": operations,
            'query': operation_name,
            "ask": ask_info
        })
    else:
        operations = Operation.objects.all()
        return render(request, 'index.html', {"operations": operations, "ask": ask_info})
    
def operation(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    return render(request, 'operation.html', {"operation": operation})

def ask(request, ask_id):
    try:
        curr_ask = Ask.objects.get(id=ask_id)
        if curr_ask.status == 'del':
            raise Ask.DoesNotExist 
    except Ask.DoesNotExist:
        return render(request, 'ask.html', {"error_message": "Нельзя просмотреть заявку."})

    ask_data = get_object_or_404(Ask, id=ask_id)

    selected_operations = Operation.objects.filter(askoperation__ask=ask_data)

    second_operands = {}
    for ask_operation in AskOperation.objects.filter(ask=ask_data):
        second_operands[ask_operation.operation.id] = ask_operation.second_operand

    context = {
        'ask': ask_data,
        'ask_number': ask_id,
        'selected_operations': selected_operations,
        'second_operands': second_operands
    }

    return render(request, 'ask.html', context)