from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Operation, Ask, AskOperation

class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'name', 'description', 'photo', 'status']

class AskOperationSerializer(serializers.ModelSerializer):
    operation = OperationSerializer(read_only=True)
    
    class Meta:
        model = AskOperation
        fields = ['id', 'ask', 'operation', 'second_operand']

class AskSerializer(serializers.ModelSerializer):
    operations = AskOperationSerializer(many=True, read_only=True, source='askoperation_set')

    class Meta:
        model = Ask
        fields = ['id', 'status', 'created_at', 'formed_at', 'completed_at', 'creator', 'moderator', 'first_operand', 'operations']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']