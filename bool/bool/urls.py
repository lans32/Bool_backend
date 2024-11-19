from django.contrib import admin
from app import views 
from django.urls import include, path
from rest_framework import routers
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('api/operations/', views.OperationList.as_view(), name='operation-list'),
    path('api/operations/<int:pk>/', views.OperationDetail.as_view(), name='operation-detail'),
    path('api/operations/<int:pk>/image/', views.OperationDetail.as_view(), name='operation-update-image'),
    path('api/operations/<int:pk>/draft/', views.OperationAddToDraft.as_view(), name='operation-add-to-draft'),
    path('api/asks/', views.AskList.as_view(), name='ask-list'),
    path('api/asks/<int:pk>/edit/', views.AskDetail.as_view(), name='ask-detail-edit'),
    path('api/asks/<int:pk>/form/', views.AskDetail.as_view(), name='ask-detail-form'),
    path('api/asks/<int:pk>/complete/', views.AskDetail.as_view(), name='ask-detail-complete'),
    path('api/asks/<int:pk>/', views.AskDetail.as_view(), name='ask-detail'),
    path('api/asks/<int:ask_id>/operations/<int:operation_id>/', views.AskOperationDetail.as_view(), name='ask-operation-detail'),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/auth/', views.UserViewSet.as_view({'post': 'create'}), name='user-register'),
    path('users/profile/', views.UserViewSet.as_view({'put': 'profile'}), name='user-profile'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
