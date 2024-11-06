from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404, HttpResponse, JsonResponse
from .models import Operation, Ask, AskOperation
from .serializers import *
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from app.permissions import *
import redis
import uuid

session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator


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
        user = request.user
        draft_ask_id = None
        count = 0
        if user:
            draft_ask = Ask.objects.filter(creator=user, status='dr').first()
            if draft_ask:
                draft_ask_id = draft_ask.id
                count = Ask.objects.get_total_operations(draft_ask)

        serializer = self.serializer_class(operations, many=True)
        response_data = {
            'operations': serializer.data,
            'draft_ask_id': draft_ask_id,
            'count': count 
        }
        return Response(response_data)
  
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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

class OperationAddToDraft(APIView):
    @swagger_auto_schema()
    def post(self, request, pk, format=None):
        user = request.user
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        operation = get_object_or_404(Operation, pk=pk)
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
    
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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
    
    """@swagger_auto_schema(request_body=serializer_class)
    def add_to_draft(self, request, pk):
        user = request.user
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
        return Response(status=status.HTTP_204_NO_CONTENT)"""
    
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put(self, request, pk, format=None):
        operation = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(operation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes([IsManager])
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
    serializer_class = AskCompactSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user

        # Получаем фильтры из запросов
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        if user.is_authenticated:
            if user.is_staff:
                asks = self.model_class.objects.all()
            else:
                asks = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
        else:
            return Response({"error": "Вы не авторизованы"}, status=401)

        if date_from:
            asks = asks.filter(created_at__gte=date_from)
        if date_to:
            asks = asks.filter(created_at__lte=date_to)

        if status:
            asks = asks.filter(status=status)

        serialized_asks = [
            {
                **self.serializer_class(ask).data, 
                'creator': ask.creator.email, 
                'moderator': ask.moderator.email if ask.moderator else None
             }
            for ask in asks
        ]

        return Response(serialized_asks)
    
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsAdmin, IsManager])
    def put(self, request, format=None):
        user = request.user
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
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        ask = get_object_or_404(self.model_class, pk=pk)
        if ask.status == 'del':
            return Response({"detail": "Эта заявка удалена и недоступна для просмотра."}, status=403)
        serializer = self.serializer_class(ask)
        data = serializer.data
        print(ask.creator)
        data['creator'] = ask.creator.email
        if ask.moderator:
            data['moderator'] = ask.moderator.email

        return Response(data)
    
    def put(self, request, pk, format=None):
        # Получаем полный путь запроса
        full_path = request.path

        # Проверяем, заканчивается ли путь на /form/, /complete/ или /edit/
        if full_path.endswith('/form/'):
            return self.put_creator(request, pk)
        elif full_path.endswith('/complete/'):
            return self.put_moderator(request, pk)
        elif full_path.endswith('/edit/'):
            return self.put_edit(request, pk)

        return Response({"error": "Неверный путь"}, status=status.HTTP_400_BAD_REQUEST)

    # PUT для создателя: формирование заявки
    def put_creator(self, request, pk, format=None):
        ask = get_object_or_404(self.model_class, pk=pk)
        user = request.user

        if user == ask.creator:
                
            if 'status' in request.data and request.data['status'] == 'f':
                ask.formed_at = timezone.now()
                updated_data = request.data.copy()
                
                for ask_operation in ask.askoperation_set.all():
                    ask_operation.calculate_result()

                serializer = self.serializer_class(ask, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": "Создатель может только формировать заявку."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)
    
    # PUT для модератора: завершение или отклонение заявки
    @method_permission_classes([IsManager])
    def put_moderator(self, request, pk):
        ask = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        
        if 'status' in request.data:
            status_value = request.data['status']

            # Модератор может завершить ('c') или отклонить ('r') заявку
            if status_value in ['c', 'r']:
                if ask.status != 'f':
                    return Response({"error": "Заявка должна быть сначала сформирована."}, status=status.HTTP_403_FORBIDDEN)

                if status_value == 'c':
                    ask.completed_at = timezone.now()
                    updated_data = request.data.copy()

                serializer = self.serializer_class(ask, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Модератор может только завершить или отклонить заявку."}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def put_edit(self, request, pk):
        ask = get_object_or_404(self.model_class, pk=pk)

        serializer = self.serializer_class(ask, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаление заявки
    def delete(self, request, pk, format=None):
        ask = get_object_or_404(self.model_class, pk=pk)
        if ask.creator != request.user:
            return Response({"detail": "Только создатель может удалить заявку."}, status=403)
        if ask.status != 'dr':
            return Response({"detail": "Данную заявку нельзя удалить."}, status=403)
        ask.status = 'del'  # Мягкое удаление
        ask.formed_at = timezone.now()
        ask.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class AskOperationDetail(APIView):
    model_class = AskOperation
    serializer_class = AskOperationSerializer

    @swagger_auto_schema(request_body=serializer_class)
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

class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    # def get_permissions(self):
    #     # Удаляем ненужные проверки, чтобы любой пользователь мог обновить свой профиль
    #     if self.action == 'create':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=serializer.data['is_superuser'],
                is_staff=serializer.data['is_staff']
            )
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Обновление данных профиля пользователя
    @action(detail=False, methods=['put'], permission_classes=[AllowAny])
    def profile(self, request, format=None):
        user = request.user
        if user is None:
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@authentication_classes([])
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    username = request.data["email"] 
    password = request.data["password"]

    user = authenticate(request, email=username, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)
        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)
        return response
        # login(request, user)
        # return HttpResponse("{'status': 'ok'}")
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

def logout_view(request):
    session_id = request.COOKIES.get("session_id")

    if session_id:
        session_storage.delete(session_id)
        response = HttpResponse("{'status': 'ok'}")
        response.delete_cookie("session_id")
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'no session found'}")
    # logout(request)
    # return Response({'status': 'Success'})