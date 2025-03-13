from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('operator_dashboard/', views.operator_dashboard ,name='operator_dashboard'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('get_image/<str:image_name>/', views.get_image, name='get_image'),  # 获取图片URL接口

    path('api/devices/', views.device_list, name='device_list'),
    path('api/devices/<int:device_id>/', views.device_detail, name='device_detail'),
    path('api/devices/<int:device_id>/update_model/', views.update_device_model, name='update_device_model'),

    # 其他路由
    path('/ajax_login/', views.ajax_login, name='ajax_login'),
    path('/ajax_register/', views.ajax_register, name='ajax_register'),
    # 其他路由
]
