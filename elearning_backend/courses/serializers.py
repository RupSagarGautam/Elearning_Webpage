from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

        
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


    def get_video(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return None 