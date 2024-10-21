from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Operation, Ask, AskOperation

class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        exclude = ['status']

class OperationCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'operator_name', 'photo']

class AskOperationSerializer(serializers.ModelSerializer):
    operation = OperationCompactSerializer(read_only=True)
    
    class Meta:
        model = AskOperation
        fields = ['id', 'ask', 'operation', 'second_operand']

class AskOperationCompactSerializer(serializers.ModelSerializer):
    operation = OperationCompactSerializer(read_only=True)
    
    class Meta:
        model = AskOperation
        fields = ['operation', 'second_operand', 'result']

class AskSerializer(serializers.ModelSerializer):
    operations = AskOperationCompactSerializer(many=True, read_only=True, source='askoperation_set')

    class Meta:
        model = Ask
        fields = ['id', 'status', 'created_at', 'formed_at', 'completed_at', 'creator', 'moderator', 'first_operand', 'operations']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']