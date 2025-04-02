"""
URL configuration for demo project.
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from testdemo import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('testdemo.urls')),
    path('api/datasets/', views.dataset_list, name='dataset_list'),
    path('api/datasets/upload/', views.dataset_upload, name='dataset_upload'),
    path('api/datasets/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
    path('api/datasets/<int:dataset_id>/download/', views.dataset_download, name='dataset_download'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
