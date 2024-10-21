from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.http import Http404
from .models import Operation, Ask, AskOperation
from .serializers import OperationSerializer, AskSerializer, AskOperationSerializer, UserSerializer
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=2)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass


def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('bool', image_name, file_object, file_object.size)
        return f"http://localhost:9000/bool/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_operation, pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_operation.id}.jpg"

    if not pic:
        return {"error": "Нет файла для изображения."}

    result = process_file_upload(pic, client, img_obj_name)
    
    if 'error' in result:
        return {"error": result['error']}

    return result 

# View для Operation (операции)
class OperationList(APIView):
    model_class = Operation
    serializer_class = OperationSerializer

    def get(self, request, format=None):
        operation_name = request.query_params.get('name')
        operations = self.model_class.objects.filter(status='a')
        if operation_name:
            operations = operations.filter(name__icontains=operation_name)
        user = UserSingleton.get_instance()
        draft_ask_id = None
        if user:
            draft_ask = Ask.objects.filter(creator=user, status='dr').first()
            if draft_ask:
                draft_ask_id = draft_ask.id

        serializer = self.serializer_class(operations, many=True)
        response_data = {
            'operations': serializer.data,
            'draft_ask_id': draft_ask_id 
        }
        return Response(response_data)
  
    def post(self, request, format=None):
        pic = request.FILES.get("photo")
        data = request.data.copy()
        data.pop('photo', None) 
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            operation = serializer.save()
            if pic:
                pic_url = add_pic(operation, pic)
                if 'error' in pic_url:
                    return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)
                operation.photo = pic_url
                operation.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OperationDetail(APIView):
    model_class = Operation
    serializer_class = OperationSerializer

    def get(self, request, pk, format=None):
        operation = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(operation)
        return Response(serializer.data)
    
    def post(self, request, pk, format=None):
        if request.path.endswith('/image/'):
            return self.update_image(request, pk)
        elif request.path.endswith('/draft/'):
            return self.add_to_draft(request, pk)
        raise Http404

    def update_image(self, request, pk):
        operation = get_object_or_404(self.model_class, pk=pk)
        pic = request.FILES.get("photo")

        if not pic:
            return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

        if operation.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            old_img_name = operation.photo.split('/')[-1]
            try:
                client.remove_object('bool', old_img_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении старого изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pic_url = add_pic(operation, pic)
        if 'error' in pic_url:
            return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)

        operation.photo = pic_url
        operation.save()

        return Response({"message": "Изображение успешно обновлено.", "photo_url": pic_url}, status=status.HTTP_200_OK)

    def add_to_draft(self, request, pk):
        user = UserSingleton.get_instance()
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        operation = get_object_or_404(self.model_class, pk=pk)
        draft_ask = Ask.objects.filter(creator=user, status='dr').first()

        if not draft_ask:
            draft_ask = Ask.objects.create(
                first_operand=False,
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_ask.save()

        if AskOperation.objects.filter(ask=draft_ask, operation=operation).exists():
            return Response(data={"error": "Операция уже добавлено в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        AskOperation.objects.create(ask=draft_ask, operation=operation, second_operand=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk, format=None):
        operation = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(operation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        operation = get_object_or_404(self.model_class, pk=pk)
        if operation.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            image_name = operation.photo.split('/')[-1]
            try:
                client.remove_object('bool', image_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        operation.status = 'd'
        operation.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Ask (заявки)
class AskList(APIView):
    model_class = Ask
    serializer_class = AskSerializer

    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        # Получаем фильтры из запросов
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        asks = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])

        if date_from:
            asks = asks.filter(created_at__gte=date_from)
        if date_to:
            asks = asks.filter(created_at__lte=date_to)

        if status:
            asks = asks.filter(status=status)

        serialized_asks = [
            {**self.serializer_class(ask).data, 'creator': ask.creator.username, 'moderator': ask.moderator.username}
            for ask in asks
        ]

        return Response(serialized_asks)
    

    def put(self, request, format=None):
        user = UserSingleton.get_instance()
        required_fields = ['first_operand']
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)
            
        ask_id = request.data.get('id')
        if ask_id:
            ask = get_object_or_404(self.model_class, pk=ask_id)
            serializer = self.serializer_class(ask, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)
            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            ask = serializer.save(creator=user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AskDetail(APIView):
    model_class = Ask
    serializer_class = AskSerializer

    def get(self, request, pk, format=None):
        ask = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(ask)
        data = serializer.data
        data['creator'] = ask.creator.username
        if ask.moderator:
            data['moderator'] = ask.moderator.username 

        return Response(data)

    def put(self, request, pk, format=None):
        ask = get_object_or_404(self.model_class, pk=pk)
        user = UserSingleton.get_instance()

        if 'status' in request.data:
            status_value = request.data['status']
            if status_value not in ['f', 'r']:
                return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)

            updated_data = request.data.copy()
            ask.completed_at = timezone.now()

            for ask_operation in ask.askoperation_set.all():
                ask_operation.calculate_result()
            
            serializer = self.serializer_class(ask, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        # Если статус не был передан, пробуем обновить остальные данные
        serializer = self.serializer_class(ask, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=user)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаление заявки
    def delete(self, request, pk, format=None):
        ask = get_object_or_404(self.model_class, pk=pk)
        ask.status = 'del'  # Мягкое удаление
        ask.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class AskOperationDetail(APIView):
    model_class = AskOperation
    serializer_class = AskOperationSerializer

    def put(self, request, ask_id, operation_id, format=None):
        ask = get_object_or_404(Ask, pk=ask_id)
        ask_operation = get_object_or_404(self.model_class, ask=ask, operation__id=operation_id)
        
        serializer = self.serializer_class(ask_operation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, ask_id, operation_id, format=None):
        ask = get_object_or_404(Ask, pk=ask_id)
        ask_operation = get_object_or_404(self.model_class, ask=ask, operation__id=operation_id)
        
        ask_operation.delete()
        return Response({"message": "Операция успешно удалено из заявки"}, status=status.HTTP_204_NO_CONTENT)

class UserView(APIView):
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                user = User(
                    username=validated_data['username'],
                    email=validated_data['email']
                )
                user.set_password(request.data.get('password'))
                user.save()
                return Response({
                    'message': 'Регистрация прошла успешно'
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'authenticate':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                user_data = UserSerializer(user).data
                return Response({
                    'message': 'Аутентификация успешна',
                    'user': user_data
                }, status=200)
            
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=400)

        elif action == 'logout':
            return Response({'message': 'Вы вышли из системы'}, status=200)

        return Response({'error': 'Некорректное действие'}, status=400)

    # Обновление данных профиля пользователя
    def put(self, request, action, format=None):
        if action == 'profile':
            user = UserSingleton.get_instance()
            if user is None:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)
