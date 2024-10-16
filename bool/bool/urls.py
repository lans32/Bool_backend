"""
URL configuration for bool project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app import views 
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('operations/', views.OperationList.as_view(), name='operation-list'),
    path('operations/<int:pk>/', views.OperationDetail.as_view(), name='operation-detail'),
    path('operations/<int:pk>/image/', views.OperationDetail.as_view(), name='operation-update-image'),
    path('operations/<int:pk>/draft/', views.OperationDetail.as_view(), name='operation-add-to-draft'),
    path('asks/', views.AskList.as_view(), name='ask-list'),
    path('asks/<int:pk>/', views.AskDetail.as_view(), name='ask-detail'),
    path('asks/<int:ask_id>/operations/<int:operation_id>/', views.AskOperationDetail.as_view(), name='ask-operation-detail'),
    path('users/<str:action>/', views.UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]
