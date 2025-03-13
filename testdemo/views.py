import os

from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from demo import settings
from testdemo.models import CustomUser, Device
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
import json


def ajax_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(username=username, password=password)

    if user is None:
        # 如果认证失败，返回错误信息
        return JsonResponse({
            'success': False,
            'errors': {'__all__': ['用户名或密码错误']}
        })

    # 认证通过后，我们使用自定义的 CustomUser 模型获取其他信息
    try:
        custom_user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'errors': {'__all__': ['用户信息不存在;']}
        })

    login(request, user)

    role = custom_user.role
    if role == 'admin':
        redirect_url = '/admin_dashboard/'
    elif role == 'operator':
        redirect_url = '/operator_dashboard/'
    else:
        redirect_url = '/maintenance_dashboard/'


    return JsonResponse({
        'success': True,
        'redirect_url': redirect_url,
        'errors': {}
    })

def ajax_register(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    confirm_password = request.POST.get('confirm_password')
    role = request.POST.get('role')  # Get the role from the form data

    errors = {}

    if password != confirm_password:
        errors['confirm_password'] = ['密码和确认密码不一致;']
    else:
        if User.objects.filter(username=username).exists():
            errors['username'] = ['用户名已存在;']

    if errors:
        return JsonResponse({
            'success': False,
            'errors': errors
        })
    else:
        # Hash the password before saving
        hashed_password = make_password(password)

        user = User(username=username)
        user.set_password(hashed_password)
        user.save()

        # Create and save the user
        user = CustomUser(username=username, password=hashed_password, role=role)
        user.save()

        return JsonResponse({
            'success': True,
            'errors': {}
        })
def index(request):
    return render(request, "testdemo/index.html")

def operator_dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'testdemo/operator_dashboard.html')
    return render(request, 'testdemo/index.html')

def admin_dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'testdemo/admin_dashboard.html')
    return render(request, 'testdemo/index.html')

def maintenance_dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'testdemo/maintenance_dashboard.html')
    return render(request, 'testdemo/index.html')

def upload_image(request):
    if request.method == 'POST' and request.FILES['image']:
        uploaded_file = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        uploaded_url = fs.url(filename)  # 获取上传后的文件 URL
        return JsonResponse({'image_url': uploaded_url})
    return JsonResponse({'error': 'No file uploaded'}, status=400)


def get_image(request, image_name):
    # 构建图片的路径
    image_path = os.path.join(settings.MEDIA_ROOT, 'uploads', image_name)

    if os.path.exists(image_path):
        # 获取图片的URL
        image_url = os.path.join(settings.MEDIA_URL, 'uploads', image_name)
        return JsonResponse({'image_url': image_url})

    # 如果文件不存在，返回错误信息
    return JsonResponse({'error': 'Image not found'}, status=404)

# 获取设备列表
def device_list(request):
    devices = Device.objects.all().values('id', 'device_name', 'model_name')
    return JsonResponse(list(devices), safe=False)

# 获取单个设备的详细信息
def device_detail(request, device_id):
    try:
        device = Device.objects.get(id=device_id)
        device_data = {
            'device_name': device.device_name,
            'model_name': device.model_name,
        }
        return JsonResponse(device_data)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)

# 更新设备模型
@csrf_exempt  # 允许接收POST请求
def update_device_model(request, device_id):
    if request.method == 'POST':
        try:
            device = Device.objects.get(id=device_id)
            data = json.loads(request.body)
            model_name = data.get('model_name')
            if model_name in ['model1', 'model2']:  # 确保模型有效
                device.model_name = model_name
                device.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid model'}, status=400)
        except Device.DoesNotExist:
            return JsonResponse({'error': 'Device not found'}, status=404)
    return JsonResponse({'error': 'Invalid method'}, status=405)