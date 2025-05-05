from django.contrib import admin
from django.utils.html import format_html
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'level', 'duration', 'display_image', 'created_at')
    list_filter = ('category', 'level', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'preview_image', 'preview_video')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', ('image', 'preview_image'), ('video', 'preview_video'))
        }),
        ('Course Details', {
            'fields': ('duration', 'level', 'category')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Thumbnail'

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" style="max-height: 200px; object-fit: contain;" />', obj.image.url)
        return "No Image"
    preview_image.short_description = 'Image Preview'

    def preview_video(self, obj):
        if obj.video:
            return format_html('''
                <video width="320" height="240" controls>
                    <source src="{}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            ''', obj.video.url)
        return "No Video"
    preview_video.short_description = 'Video Preview'
