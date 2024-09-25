URL = 'http://192.168.51.76:9000/bool/{}.gif'

OPERATIONS = [
    {
        'id': 1,
        'name': 'Дизъюнкция',
        'description': 'Оператор OR',
        'photo': URL.format('1'),
        'photot': URL.format('ort'),
        'photol': URL.format('orl'),
    },

    {
        'id': 2,
        'name': 'Конъюнкция',
        'description': 'Оператор AND',
        'photo': URL.format('2'),
        'photot': URL.format('andt'),
        'photol': URL.format('andl'),
    }, 

    {
        'id': 3, 
        'name': 'Исключающие "ИЛИ"',
        'description': 'Оператор XOR',
        'photo': URL.format('3'),
        'photot': URL.format('xort'),
        'photol': URL.format('xorl'),
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