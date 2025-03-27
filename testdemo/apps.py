from django.apps import AppConfig


class TestdemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "testdemo"


    def ready(self):
        from .task import check_new_images_periodically, move_pending_images
        check_new_images_periodically(interval_seconds=30)
        move_pending_images(interval_seconds=20)