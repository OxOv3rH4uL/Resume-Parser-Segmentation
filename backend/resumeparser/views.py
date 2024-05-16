# views.py
from django.shortcuts import render
from .apps import ResumeparserConfig
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import os

from .serializers import FileUploadSerializer
import time
class FileUploadView(APIView):
    def download_pdf(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()  
            file_name = url.split('/')[-1] 
            file_path = file_name
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return file_path
        except requests.exceptions.RequestException as e:
            print(f"Error downloading PDF from {url}: {e}")
            return None
            
    def post(self, request, format=None):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            pdf_url = serializer.validated_data['pdf_url']
            file_path = self.download_pdf(pdf_url)
            if file_path:
                msg, coords = ResumeparserConfig.get_coordinates(file_path)
                time.sleep(5)
                os.remove(file_path)
                # os.remove('1resume.jpg')
                return Response({'MESSAGE': msg, 'COORDINATES': coords}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to download PDF from the provided URL'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    