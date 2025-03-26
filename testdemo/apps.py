from django.apps import AppConfig


class TestdemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "testdemo"


    def ready(self):
        from .task import check_new_images_periodically
        check_new_images_periodically(interval_seconds=300)  # 每5分钟检查一次