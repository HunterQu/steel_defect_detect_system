import os
import time
import shutil
import threading
from django.conf import settings
from django.utils import timezone
from .models import Image, Device


def check_new_images_periodically(interval_seconds=300):
    def task():
        while True:
            images_path = os.path.join(settings.MEDIA_ROOT, 'images/')
            existing_images = set(Image.objects.values_list('image_file', flat=True))

            for filename in os.listdir(images_path):
                file_path = os.path.join('images', filename)

                # 跳过已处理的图片
                if file_path in existing_images:
                    continue

                # 假设图片命名规则为：设备名_批次号_时间戳.jpg
                # 例：设备A_001_20250326.jpg
                parts = filename.rsplit('_', 2)  # 切割设备名、批次号、时间戳
                if len(parts) != 3:
                    continue  # 如果命名格式不对，跳过该图片

                device_name, batch_number, timestamp_str = parts
                timestamp = timezone.datetime.strptime(timestamp_str.replace('.jpg', ''), '%Y%m%d')

                # 查找设备是否存在，如果存在则更新，如果不存在则创建
                device, created = Device.objects.get_or_create(
                    device_name=device_name,
                    defaults={'model_name': 'default_model', 'total_runtime': timezone.timedelta(), 'total_idle_time': timezone.timedelta()}
                )

                # 如果设备已经存在，并且批次号发生变化或其他信息需要更新，可做相应处理
                if not created:
                    # 更新设备的其他字段（如果需要）
                    device.batch_number = batch_number
                    device.save()

                # 创建图片记录
                image = Image.objects.create(
                    image_name=filename,
                    batch_number=batch_number,
                    device=device,
                    timestamp=timestamp,
                    image_file=file_path,
                )

                print(f"New image imported: {filename} and associated with device: {device_name}")

            time.sleep(interval_seconds)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()


def move_pending_images(interval_seconds=300):
    def task():
        while True:
            source_dir = os.path.join(settings.MEDIA_ROOT, '待上传')
            target_dir = os.path.join(settings.MEDIA_ROOT, 'images')

            if not os.path.exists(source_dir):
                print(f"源目录 {source_dir} 不存在")
            else:
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    print(f"创建目标目录 {target_dir}")

                valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
                for filename in os.listdir(source_dir):
                    if filename.lower().endswith(valid_extensions):
                        src_path = os.path.join(source_dir, filename)
                        dest_path = os.path.join(target_dir, filename)
                        try:
                            shutil.move(src_path, dest_path)
                            print(f"成功移动 {filename}")
                        except Exception as e:
                            print(f"移动 {filename} 时出错: {e}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()