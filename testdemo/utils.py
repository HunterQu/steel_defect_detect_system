import os

from django.core.files import File
from django.db.models import Count
from django.db.models import F
from django.utils import timezone

from testdemo.models import ProcessingResult, Device, DeviceUsage, CustomUser, Image


def get_defect_and_quality_rate(period='day'):
    # 获取当前时间
    now = timezone.now()

    # 根据选择的 period 获取按年、月、日的数据
    if period == 'day':
        period_format = "%Y-%m-%d"
    elif period == 'month':
        period_format = "%Y-%m"
    elif period == 'year':
        period_format = "%Y"
    else:
        raise ValueError("Invalid period. Choose from 'day', 'month', or 'year'.")

    # 按时间段聚合
    processing_results = ProcessingResult.objects.annotate(
        period=F('timestamp__date')
    ).values('period').annotate(
        total_count=Count('id'),
        defect_count=Count('id', filter=F('result') == 'problem'),
        quality_count=Count('id', filter=F('result') == 'no_problem')
    )

    # 计算缺陷率和良品率
    data = []
    for result in processing_results:
        defect_rate = (result['defect_count'] / result['total_count']) * 100 if result['total_count'] > 0 else 0
        quality_rate = (result['quality_count'] / result['total_count']) * 100 if result['total_count'] > 0 else 0
        data.append({
            'period': result['period'],
            'defect_rate': defect_rate,
            'quality_rate': quality_rate,
        })

    return data

def get_device_utilization(device_id):
    # 获取设备
    device = Device.objects.get(id=device_id)

    # 计算设备的运行时间和空闲时间
    usage_data = DeviceUsage.objects.filter(device=device)

    total_runtime = sum((usage.end_time - usage.start_time).total_seconds()
                        for usage in usage_data if usage.status == 'running')
    total_idle_time = sum((usage.end_time - usage.start_time).total_seconds()
                          for usage in usage_data if usage.status == 'idle')

    total_time = total_runtime + total_idle_time

    utilization_rate = (total_runtime / total_time) * 100 if total_time > 0 else 0

    return {
        'device_name': device.device_name,
        'total_runtime': total_runtime,
        'total_idle_time': total_idle_time,
        'utilization_rate': utilization_rate,
    }

def get_employee_work_status(user_id, period='day'):
    # 获取员工
    user = CustomUser.objects.get(id=user_id)

    # 获取员工处理的图片数据
    if period == 'day':
        period_format = "%Y-%m-%d"
    elif period == 'month':
        period_format = "%Y-%m"
    elif period == 'year':
        period_format = "%Y"
    else:
        raise ValueError("Invalid period. Choose from 'day', 'month', or 'year'.")

    work_data = ProcessingResult.objects.filter(operator=user).values('timestamp__date').annotate(
        total_images=Count('id'),
        problem_images=Count('id', filter=F('result') == 'problem'),
        approved_images=Count('id', filter=F('approval_result') == 'approved')
    )

    data = []
    for entry in work_data:
        data.append({
            'date': entry['timestamp__date'],
            'total_images': entry['total_images'],
            'problem_images': entry['problem_images'],
            'approved_images': entry['approved_images'],
        })

    return data

def process_image(input_file_path, output_file_path, model_name):
    # 这里的功能将是实际的图片处理，具体细节取决于需求
    # 例如：保存到output_file_path并返回处理结果
    processed_image_path = output_file_path  # 假设这是处理后的图片文件路径
    return processed_image_path, 'no_problem', 'approved'  # 只是一个示例返回


def process_device_snapshot(device_id, image_id, model_name, output_directory):
    """
    处理设备生成的快照并将处理结果储存到数据库中。

    :param device_id: 设备ID
    :param image_id: 图片ID
    :param model_name: 设备的模型名称
    :param output_directory: 处理后的图片储存目录
    :return: 处理结果的模型实例
    """

    # 获取设备和图片实例
    device = Device.objects.get(id=device_id)
    image = Image.objects.get(id=image_id)

    # 生成处理后的图片存储地址
    output_file_name = f"{device.device_name}_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"
    output_file_path = os.path.join(output_directory, output_file_name)

    # 调用处理图片的函数（空壳函数）
    processed_image_path, result, approval_result = process_image(image.image_file.path, output_file_path, model_name)

    # 创建处理结果对象并保存
    processing_result = ProcessingResult.objects.create(
        image=image,
        timestamp=image.timestamp,
        result=result,
        approval_result=approval_result,
        operator=None,
    )

    return processing_result