from django.db import models
from django.utils import timezone


class CustomUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=[
        ('operator', 'Operator'),
        ('admin', 'Admin'),
        ('maintenance', 'Maintenance'),
    ], default='operator')

    def __str__(self):
        return self.username

# 设备模型
class Device(models.Model):
    device_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    total_runtime = models.DurationField(default=timezone.timedelta())  # 总运行时间
    total_idle_time = models.DurationField(default=timezone.timedelta())  # 总空闲时间

    def __str__(self):
        return self.device_name

# 图片模型
class Image(models.Model):
    image_name = models.CharField(max_length=255)
    batch_number = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    device = models.ForeignKey(Device, related_name='images', on_delete=models.CASCADE)
    image_file = models.ImageField(upload_to='images/')  # 保存图片文件的路径

    def __str__(self):
        return self.image_name



class DeviceUsage(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[('running', 'Running'), ('idle', 'Idle')])

    def __str__(self):
        return f"Usage for {self.device.device_name} from {self.start_time} to {self.end_time}"

# 处理结果模型
class ProcessingResult(models.Model):
    RESULT_CHOICES = [
        ('no_problem', 'No Problem'),
        ('problem', 'Problem'),
    ]

    APPROVAL_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    image = models.OneToOneField(Image, related_name='processing_result', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)  # 时间戳
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    approval_result = models.CharField(max_length=20, choices=APPROVAL_CHOICES)
    operator = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Processing Result for {self.image.image_name}"

