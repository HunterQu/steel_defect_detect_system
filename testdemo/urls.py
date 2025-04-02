from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('operator_dashboard/', views.operator_dashboard ,name='operator_dashboard'),
    path('admin_dashboard/', views.admin_dashboard ,name='admin_dashboard'),
    path('maintenance_dashboard/', views.maintenance_dashboard ,name='maintenance_dashboard'),


    path('upload_image/', views.upload_image, name='upload_image'),
    path('get_image/<str:image_name>/', views.get_image, name='get_image'),  # 获取图片URL接口

    path('api/devices/', views.device_list, name='device_list'),
    path('api/devices/<int:device_id>/', views.device_detail, name='device_detail'),
    path('api/devices/<int:device_id>/update_model/', views.update_device_model, name='update_device_model'),

    path('api/processing_results/problem/', views.get_images_for_audit, name='get_images_for_audit'),
    path('api/processing_results/<int:processing_result_id>/', views.get_processing_result, name='get_processing_result'),
    path('api/processing_results/<int:processing_result_id>/update_approval/', views.update_approval_result, name='update_approval_result'),
    path('api/upload_dataset_folder/', views.upload_dataset_folder, name='upload_dataset_folder'),
    path('api/datasets/', views.dataset_list, name='dataset_list'),
    path('api/datasets/upload/', views.dataset_upload, name='dataset_upload'),
    path('api/datasets/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
    path('api/datasets/<int:dataset_id>/download/', views.dataset_download, name='dataset_download'),

    path('api/statistics/defects/<str:period>/', views.get_defect_statistics, name='defect_statistics'),
    path('api/statistics/utilization/<int:device_id>/', views.get_device_utilization_statistics, name='device_utilization'),
    path('api/statistics/utilization/all/', views.get_all_device_utilization_statistics, name='all_device_utilization'),
    path('api/statistics/employee/<int:user_id>/<str:period>/', views.get_employee_work_status_statistics, name='employee_work_status'),

    # 其他路由
    path('ajax_login/', views.ajax_login, name='ajax_login'),
    path('ajax_register/', views.ajax_register, name='ajax_register'),
    # 其他路由
]
