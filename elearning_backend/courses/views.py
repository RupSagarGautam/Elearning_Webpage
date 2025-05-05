from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from .models import Course
from .serializers import CourseSerializer
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
import json
import re

# ==============================================
# Utility Functions
# ==============================================

def validate_username(username):
    if not username:
        return False, "Username is required"
    
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None

# ==============================================
# Course ViewSet
# ==============================================

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        try:
            # Validate request data
            if not request.data:
                return Response({
                    'status': 'error',
                    'message': 'No data provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create serializer instance
            serializer = self.get_serializer(data=request.data)
            
            # Validate serializer
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save the course
            try:
                self.perform_create(serializer)
            except IntegrityError as e:
                return Response({
                    'status': 'error',
                    'message': 'Database error',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                return Response({
                    'status': 'error',
                    'message': 'Validation error',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'success',
                'message': 'Course created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        except json.JSONDecodeError:
            return Response({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'count': len(serializer.data),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Failed to fetch courses',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            self.perform_update(serializer)
            return Response({
                'status': 'success',
                'message': 'Course updated successfully',
                'data': serializer.data
            })
        except Course.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({
                'status': 'success',
                'message': 'Course deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Course.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==============================================
# Authentication Views
# ==============================================

@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    return Response({
        'csrf_token': get_token(request)
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    try:
        # Use request.data instead of request.body
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Print parsed data for debugging
        print("Parsed data:", {'username': username, 'email': email, 'password': '***'})
        
        # Check if all required fields are present
        if not all([username, email, password]):
            return Response({
                'error': 'Please provide all required fields: username, email, and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate username
        is_valid_username, username_error = validate_username(username)
        if not is_valid_username:
            return Response({
                'error': username_error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return Response({
                'error': 'Please enter a valid email address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({
                'error': list(e.messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user with hashed password
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password  # Django's create_user automatically hashes the password
        )
        
        return Response({
            'message': 'User created successfully',
            'username': user.username,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print("Unexpected error:", str(e))
        return Response({
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        # Use request.data instead of request.body
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Print parsed data for debugging
        print("Parsed data:", {'username': username, 'password': '***'})
        
        if not username or not password:
            return Response({
                'error': 'Please provide both username and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate username format
        is_valid_username, username_error = validate_username(username)
        if not is_valid_username:
            return Response({
                'error': username_error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                'message': 'Login successful',
                'username': user.username,
                'email': user.email
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        print("Unexpected error:", str(e))
        return Response({
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({
        'message': 'Logged out successfully'
    })
