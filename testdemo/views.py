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
from testdemo.models import CustomUser, Device, ProcessingResult, Dataset, DatasetFile
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
        try:
            from django.db import transaction
            with transaction.atomic():
                datasets = Dataset.objects.all().order_by('-upload_date')
                print("Datasets query:", datasets.query)  # 打印SQL查询
                print("Datasets count:", datasets.count())  # 打印记录数
                for dataset in datasets:
                    print(f"Dataset: {dataset.name}, File count: {dataset.file_count}")
                # 强制重新计算file_count
                for dataset in datasets:
                    dataset.file_count = dataset.files.count()
                    dataset.save()
                return render(request, 'testdemo/maintenance_dashboard.html', {
                    'datasets': datasets
                })
        except Exception as e:
            print("Database error:", str(e))
            return render(request, 'testdemo/maintenance_dashboard.html', {
                'datasets': [],
                'error': '数据库访问出错'
            })
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
            'runtime': device.total_runtime.total_seconds() / 3600,  # 转换为小时
            'idle_time': device.total_idle_time.total_seconds() / 3600  # 转换为小时
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
        if not dataset_files:
            return JsonResponse({'success': False, 'error': '未接收到文件'}, status=400)

        try:
            import re
            from django.db import transaction
            
            # 优先使用用户输入的名称
            folder_name = request.POST.get('dataset_name', '未命名数据集')
            
            # 如果没有用户输入的名称，则尝试从文件路径提取
            if folder_name == '未命名数据集':
                first_file = dataset_files[0]
                # 统一处理不同操作系统的路径分隔符
                filename = first_file.name.replace('\\', '/')
                if '/' in filename:
                    folder_name = filename.split('/')[0]
            
            # 去除非安全字符（防止路径注入）
            folder_name = re.sub(r'[^\w\-_]', '_', folder_name)
            print(f"最终使用的数据集名称: {folder_name} (已安全处理)")
            
            # 使用事务确保原子性
            with transaction.atomic():
                dataset = Dataset.objects.create(
                    name=folder_name,
                    description=request.POST.get('description', ''),
                    file_count=len(dataset_files)
                )
                
                # 创建存储目录（保留原始结构）
                dataset_folder = os.path.join(
                    settings.MEDIA_ROOT, 
                    'datasets', 
                    str(dataset.id), 
                    folder_name  # 保留原始文件夹名
                )
                os.makedirs(dataset_folder, exist_ok=True)
                
                # 批量保存文件（提高性能）
                fs = FileSystemStorage(location=dataset_folder)
                dataset_files_to_create = []
                for file in dataset_files:
                    # 保存文件
                    filename = fs.save(file.name, file)
                    # 记录相对路径（相对于 MEDIA_ROOT）
                    relative_path = os.path.join('datasets', str(dataset.id), folder_name, filename)
                    dataset_files_to_create.append(
                        DatasetFile(dataset=dataset, file=relative_path)
                    )
                
                # 批量创建数据库记录
                DatasetFile.objects.bulk_create(dataset_files_to_create)
            
            # 验证实际保存的文件数
            actual_count = DatasetFile.objects.filter(dataset=dataset).count()
            return JsonResponse({
                'success': True,
                'dataset_id': dataset.id,
                'dataset_name': dataset.name,
                'expected_files': len(dataset_files),
                'saved_files': actual_count,
                'message': f'成功上传 {actual_count}/{len(dataset_files)} 个文件到数据集"{dataset.name}"'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': '无效请求方法'
    }, status=405)

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
            'total_runtime': utilization_data.get('total_runtime', 0) / 3600,  # 秒转换为小时
            'total_idle_time': utilization_data.get('total_idle_time', 0) / 3600,  # 秒转换为小时
            'utilization_rate': utilization_data.get('utilization_rate', 0)
        })
    return JsonResponse(data, safe=False)

def get_employee_work_status_statistics(request, user_id, period='day'):
    data = get_employee_work_status(user_id, period)
    return JsonResponse(data, safe=False)

def dataset_list(request):
    datasets = Dataset.objects.all().values('id', 'name', 'description', 'upload_date')
    return JsonResponse(list(datasets), safe=False)

@csrf_exempt
def dataset_upload(request):
    if request.method == 'POST' and request.FILES.getlist('dataset_files'):
        from django.db import transaction
        from django.db.utils import OperationalError
        import time
        
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # 获取上传的第一个文件名作为数据集名称
                    first_file = request.FILES.getlist('dataset_files')[0]
                    dataset_name = os.path.splitext(first_file.name)[0]
                    
                    # 检查是否已有同名数据集
                    if Dataset.objects.filter(name=dataset_name).exists():
                        return JsonResponse({
                            'success': False,
                            'error': f'数据集"{dataset_name}"已存在'
                        }, status=400)
                    
                    # 创建数据集记录但不立即保存文件
                    dataset = Dataset(
                        name=dataset_name,
                        description=request.POST.get('description', ''),
                        file_count=0  # 初始化为0，成功后再更新
                    )
                    dataset.save()
                    
                    # 创建存储目录
                    dataset_dir = os.path.join(settings.MEDIA_ROOT, 'datasets', str(dataset.id))
                    os.makedirs(dataset_dir, exist_ok=True)
                    
                    # 保存文件到临时目录
                    temp_dir = os.path.join(dataset_dir, 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    saved_files = []
                    for dataset_file in request.FILES.getlist('dataset_files'):
                        # 保存到临时文件
                        temp_path = os.path.join(temp_dir, dataset_file.name)
                        with open(temp_path, 'wb+') as destination:
                            for chunk in dataset_file.chunks():
                                destination.write(chunk)
                        
                        # 记录文件信息
                        relative_path = os.path.join('datasets', str(dataset.id), dataset_file.name)
                        saved_files.append(DatasetFile(
                            dataset=dataset,
                            file=relative_path
                        ))
                    
                    # 批量创建文件记录
                    DatasetFile.objects.bulk_create(saved_files)
                    
                    # 移动文件到最终位置
                    for f in os.listdir(temp_dir):
                        src = os.path.join(temp_dir, f)
                        dst = os.path.join(dataset_dir, f)
                        os.rename(src, dst)
                    
                    # 删除临时目录
                    os.rmdir(temp_dir)
                    
                    # 更新文件计数
                    dataset.file_count = len(saved_files)
                    dataset.save()
                    
                    return JsonResponse({
                        'success': True,
                        'dataset_id': dataset.id,
                        'file_count': dataset.file_count,
                        'dataset_name': dataset.name,
                        'message': f'成功上传 {dataset.file_count} 个文件'
                    })
                    
            except OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)

def dataset_detail(request, dataset_id):
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        files = dataset.files.all().values('id', 'file', 'uploaded_at')
        return JsonResponse({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'upload_date': dataset.upload_date,
            'file_count': dataset.file_count,
            'files': list(files)
        })
    except Dataset.DoesNotExist:
        return JsonResponse({'error': 'Dataset not found'}, status=404)

@csrf_exempt
def dataset_delete(request, dataset_id):
    if request.method == 'DELETE':
        try:
            # 使用事务确保原子性
            from django.db import transaction
            with transaction.atomic():
                # 检查数据集是否存在
                if not Dataset.objects.filter(id=dataset_id).exists():
                    return JsonResponse({'success': False, 'error': 'Dataset not found'}, status=404)
                
                dataset = Dataset.objects.get(id=dataset_id)
                # 获取数据集文件夹路径
                dataset_dir = os.path.join(settings.MEDIA_ROOT, 'datasets', str(dataset_id))
                
                # 删除关联的物理文件
                for file in dataset.files.all():
                    if os.path.exists(file.file.path):
                        os.remove(file.file.path)
                
                # 删除数据库记录
                dataset.files.all().delete()
                dataset.delete()
                
                # 删除数据集文件夹（如果存在）
                if os.path.exists(dataset_dir):
                    import shutil
                    shutil.rmtree(dataset_dir)
                
                return JsonResponse({'success': True})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

import zipfile
import tempfile
from django.http import HttpResponse

def dataset_download(request, dataset_id):
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        dataset_files = dataset.files.all()
        
        if not dataset_files:
            return JsonResponse({'error': 'Dataset is empty'}, status=404)
            
        # 创建临时zip文件
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dataset_file in dataset_files:
                if os.path.exists(dataset_file.file.path):
                    zipf.write(dataset_file.file.path, os.path.basename(dataset_file.file.path))
        
        temp_file.close()
        
        # 返回zip文件
        response = HttpResponse(open(temp_file.name, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{dataset.name}.zip"'
        
        # 删除临时文件
        os.unlink(temp_file.name)
        
        return response
        
    except Dataset.DoesNotExist:
        return JsonResponse({'error': 'Dataset not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
