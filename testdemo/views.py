import os

from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, FileResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from demo import settings
from testdemo.models import CustomUser, Device, ProcessingResult, Dataset
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
import json

from testdemo.utils import get_defect_and_quality_rate, get_device_utilization, get_employee_work_status


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
        user = User(username=username)
        user.set_password(password)
        user.save()

        # Create and save the user
        user = CustomUser(username=username, password=password, role=role)
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
    image_path = os.path.join(settings.MEDIA_ROOT, 'uploads', image_name)

    if os.path.exists(image_path):
        image_url = os.path.join(settings.MEDIA_URL, 'uploads', image_name)
        return JsonResponse({'image_url': image_url})

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

# 获取所有处理结果为"有问题"的图片
def get_images_for_audit(request):
    problem_images = ProcessingResult.objects.filter(result='problem').select_related('image').values(
        'id',
        'image_id',
        'image__image_name',
        'image__image_file',
        'image__batch_number',
        'result'
    )
    return JsonResponse([
        {
            'id': img['id'],
            'image_id': img['image_id'],
            'image': {
                'image_name': img['image__image_name'],
                'image_file': img['image__image_file'],
                'batch_number': img['image__batch_number']
            },
            'result': img['result']
        }
        for img in problem_images
    ], safe=False)

# 提交审批结果
@csrf_exempt
def update_approval_result(request, processing_result_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            approval_result = data.get('approval_result')
            if not approval_result:
                return JsonResponse({'success': False, 'error': '缺少审批结果参数'})
            
            try:
                user = CustomUser.objects.get(username=request.user.username)
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'error': '用户不存在'})
            
            try:
                processing_result = ProcessingResult.objects.get(id=processing_result_id)
                processing_result.approval_result = approval_result
                processing_result.operator = user
                processing_result.save()
                return JsonResponse({'success': True})
            except ProcessingResult.DoesNotExist:
                return JsonResponse({'success': False, 'error': '处理结果未找到'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '无效的JSON数据'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '无效的请求方法'})

@csrf_exempt
def upload_dataset_folder(request):
    if request.method == 'POST':
        dataset_files = request.FILES.getlist('datasets')
        if dataset_files:
            dataset_folder = os.path.join(settings.MEDIA_ROOT, 'datasets_folder')
            os.makedirs(dataset_folder, exist_ok=True)

            for file in dataset_files:
                relative_path = file.name  # 这里的name即前端设置的webkitRelativePath
                file_path = os.path.join(dataset_folder, relative_path)

                # 确保子文件夹存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': '未接收到文件。'})
    return JsonResponse({'success': False, 'error': '无效请求方法。'})

def get_defect_statistics(request, period='day'):
    data = get_defect_and_quality_rate(period)
    return JsonResponse(data, safe=False)

def get_device_utilization_statistics(request, device_id):
    data = get_device_utilization(device_id)
    return JsonResponse(data)

def get_all_device_utilization_statistics(request):
    devices = Device.objects.all()
    data = []
    for device in devices:
        utilization_data = get_device_utilization(device.id)
        data.append({
            'device_id': device.id,
            'device_name': device.device_name,
            'total_runtime': utilization_data.get('total_runtime', 0),
            'total_idle_time': utilization_data.get('total_idle_time', 0),
            'utilization_rate': utilization_data.get('utilization_rate', 0)
        })
    return JsonResponse(data, safe=False)

def get_employee_work_status_statistics(request, user_id, period='day'):
    data = get_employee_work_status(user_id, period)
    return JsonResponse(data, safe=False)

def dataset_list(request):
    datasets = Dataset.objects.all().values('id', 'name', 'description', 'created_at')
    return JsonResponse(list(datasets), safe=False)

@csrf_exempt
def dataset_upload(request):
    if request.method == 'POST' and request.FILES.getlist('dataset_files'):
        datasets = []
        for dataset_file in request.FILES.getlist('dataset_files'):
            fs = FileSystemStorage()
            filename = fs.save(f'datasets/{dataset_file.name}', dataset_file)
            dataset = Dataset(
                name=dataset_file.name,
                description=request.POST.get('description', ''),
                file_path=fs.path(filename)
            )
            dataset.save()
            datasets.append(dataset.id)
        return JsonResponse({'success': True, 'dataset_ids': datasets})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def dataset_detail(request, dataset_id):
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        return JsonResponse({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'created_at': dataset.created_at,
            'file_path': dataset.file_path
        })
    except Dataset.DoesNotExist:
        return JsonResponse({'error': 'Dataset not found'}, status=404)

def dataset_download(request, dataset_id):
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        if os.path.exists(dataset.file_path):
            return FileResponse(open(dataset.file_path, 'rb'), as_attachment=True)
        return JsonResponse({'error': 'File not found'}, status=404)
    except Dataset.DoesNotExist:
        return JsonResponse({'error': 'Dataset not found'}, status=404)

def get_processing_result(request, processing_result_id):
    try:
        result = ProcessingResult.objects.get(id=processing_result_id)
        return JsonResponse({
            'id': result.id,
            'image_id': result.image_id,
            'result': result.result,
            'approval_result': result.approval_result,
            'image': {
                'image_name': result.image.image_name,
                'image_url': result.image.image_file.url if result.image.image_file else None,
                'batch_number': result.image.batch_number
            }
        })
    except ProcessingResult.DoesNotExist:
        return JsonResponse({'error': 'Processing result not found'}, status=404)
