from django.contrib import admin
from .models import CustomUser, Image, Device, DeviceUsage, ProcessingResult

class ImageAdmin(admin.ModelAdmin):
    list_display = ('image_name', 'batch_number', 'timestamp', 'get_approval_status')
    list_filter = ('processing_result__approval_result',)
    search_fields = ('image_name', 'batch_number')

    def get_approval_status(self, obj):
        if hasattr(obj, 'processing_result'):
            return obj.processing_result.get_approval_result_display()
        return 'Pending'
    get_approval_status.short_description = 'Approval Status'

admin.site.register(CustomUser)
admin.site.register(Image, ImageAdmin)
admin.site.register(Device)
admin.site.register(DeviceUsage)
admin.site.register(ProcessingResult)
