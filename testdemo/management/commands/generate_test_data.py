#通过python manage.py generate_test_data --count 100生成测试数据
from django.core.management.base import BaseCommand
from django.utils import timezone
from testdemo.models import Image, Device, ProcessingResult, DeviceUsage
import os
import random
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate test data for Image and Device models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of test data sets to generate'
        )

    def handle(self, *args, **options):
        # 确保图片目录存在
        images_dir = os.path.join(settings.MEDIA_ROOT, 'images')
        os.makedirs(images_dir, exist_ok=True)

        # 测试设备列表
        devices = ['设备A', '设备B', '设备C']
        batch_numbers = ['001', '002', '003']
        
        # 生成测试数据
        for _ in range(options['count']):
            for device_name in devices:
                for batch_number in batch_numbers:
                    # 创建时间戳
                    timestamp = timezone.now()
                    timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
                    
                    # 创建图片文件名
                    filename = f"{device_name}_{batch_number}_{timestamp_str}.jpg"
                    file_path = os.path.join('images', filename)
                    
                    # 创建空图片文件
                    open(os.path.join(images_dir, filename), 'w').close()
                    
                    # 创建图片记录
                    image = Image.objects.create(
                        image_name=filename,
                        batch_number=batch_number,
                        timestamp=timestamp,
                        image_file=file_path
                    )
                    
                    # 随机生成处理结果
                    result = random.choice(['problem', 'no problem'])
                    approval = random.choice(['approved', 'problem', 'pending'])
                    
                    # 创建处理结果记录
                    ProcessingResult.objects.create(
                        image=image,
                        result=result,
                        approval_result=approval
                    )
                    
                    # 创建或获取设备
                    runtime_hours = random.randint(1, 1000)
                    idle_hours = random.randint(1, 500)
                    device, created = Device.objects.get_or_create(
                        device_name=device_name,
                        defaults={
                            'model_name': f'型号_{device_name}',
                            'total_runtime': timezone.timedelta(hours=runtime_hours),
                            'total_idle_time': timezone.timedelta(hours=idle_hours),
                            'image': image
                        }
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'Created test data: {filename}'))
                    
                    # 为设备生成使用记录
                    for _ in range(random.randint(1, 5)):  # 每个设备生成1-5条使用记录
                        start_time = timestamp - timezone.timedelta(
                            hours=random.randint(1, 24),
                            minutes=random.randint(0, 59)
                        )
                        end_time = start_time + timezone.timedelta(
                            hours=random.randint(1, 8),
                            minutes=random.randint(0, 59)
                        )
                        status = random.choice(['running', 'idle'])
                        
                        DeviceUsage.objects.create(
                            device=device,
                            start_time=start_time,
                            end_time=end_time,
                            status=status
                        )

        self.stdout.write(self.style.SUCCESS('Successfully generated test data'))
