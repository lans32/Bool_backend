URL = 'http://127.0.0.1:9000/bool/{}.gif'

OPERATIONS = [
    {
        'id': 1,
        'name': 'Дизъюнкция',
        'description': 'Оператор OR',
        'photo': 'http://127.0.0.1:9000/bool/1.gif',
    },

    {
        'id': 2,
        'name': 'Конъюнкция',
        'description': 'Оператор AND',
        'photo': URL.format('2'),
    }, 

    {
        'id': 3, 
        'name': 'Исключающие "ИЛИ"',
        'description': 'Оператор XOR',
        'photo': URL.format('3'),
    },

    {
        'id': 4, 
        'name': 'Импликация',
        'description': 'Оператор A → B',
        'photo': URL.format('4'),
    }
]

ASK_DATA = [
    {
        "id": 1,
        "first" : 1,
        "ask1" : {
            "operation_id": 1,
            "second" : 0,
            "resault" : 1
        },
        "ask2" : {
            "operation_id": 2,
            "second" : 1,
            "resault" : 1
        },
        "ask3" : {
            "operation_id": 3,
            "second" : 1,
            "resault" : 0
        }
    }
] 