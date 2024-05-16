from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    pdf_url = serializers.URLField()
    