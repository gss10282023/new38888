# BIOTech Futures Hub - Django 后端开发计划

**目标：功能优先，快速上线**  
**技术栈：Django + Django REST Framework + PostgreSQL + Redis**  
**服务器：Vultr VPS + Vultr Object Storage**

---

## 技术栈确认

```python
# 核心框架
Django==5.0
djangorestframework==3.14
djangorestframework-simplejwt==5.3  # JWT 认证
drf-spectacular==0.27.0  # OpenAPI 文档自动生成（可选）

# 数据库
psycopg2-binary==2.9  # PostgreSQL
redis==5.0  # 缓存

# 文件存储
django-storages==1.14  # S3 兼容存储
boto3==1.34  # AWS SDK (Vultr S3 兼容)

# 邮件
django-anymail==10.2  # 邮件服务（支持 SendGrid/Mailgun）

# 工具
django-cors-headers==4.3  # CORS
python-dotenv==1.0  # 环境变量
```

---

## Step 1: 项目初始化与基础配置

### 1.1 创建 Django 项目

```bash
# 创建项目
django-admin startproject btf_backend
cd btf_backend

# 创建核心 apps
python manage.py startapp authentication
python manage.py startapp users
python manage.py startapp groups
python manage.py startapp chat
python manage.py startapp resources
python manage.py startapp events
python manage.py startapp announcements
```

### 1.2 项目结构

```
btf_backend/
├── authentication/       # 认证相关
├── users/               # 用户管理
├── groups/              # 群组管理
├── chat/                # 聊天消息
├── resources/           # 资源库
├── events/              # 活动管理
├── announcements/       # 公告系统
├── core/                # 通用工具
│   ├── permissions.py   # 权限类
│   ├── pagination.py    # 分页配置
│   └── storage.py       # S3 存储配置
├── btf_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
```

### 1.3 配置 settings.py

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'storages',
    
    # Local apps
    'authentication',
    'users',
    'groups',
    'chat',
    'resources',
    'events',
    'announcements',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # 前端开发服务器
    "https://yourdomain.com",
]

# Vultr Object Storage (S3 Compatible)
AWS_ACCESS_KEY_ID = os.getenv('VULTR_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('VULTR_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('VULTR_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('VULTR_S3_ENDPOINT')  # e.g., https://sjc1.vultrobjects.com
AWS_S3_REGION_NAME = 'sjc1'  # 根据你的 Vultr 区域
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_ENDPOINT_URL}'
AWS_DEFAULT_ACL = 'public-read'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### 1.4 环境变量 (.env)

```bash
# Database
DB_NAME=btf_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# JWT
SECRET_KEY=your-django-secret-key

# Vultr Object Storage
VULTR_ACCESS_KEY=your_vultr_access_key
VULTR_SECRET_KEY=your_vultr_secret_key
VULTR_BUCKET_NAME=btf-storage
VULTR_S3_ENDPOINT=https://sjc1.vultrobjects.com

# Email (可选：SendGrid)
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
SENDGRID_API_KEY=your_sendgrid_key
DEFAULT_FROM_EMAIL=noreply@biotechfutures.org
```

**✅ Step 1 完成标准：**
- Django 项目能成功运行
- 数据库连接成功
- Redis 连接成功

---

## Step 2: 认证系统（Magic Link + JWT）

### 2.1 创建用户模型

```python
# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    track = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending')],
        default='pending'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    areas_of_interest = models.JSONField(default=list, blank=True)
    school_name = models.CharField(max_length=255, blank=True)
    year_level = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    availability = models.TextField(blank=True)
```

### 2.2 Magic Link 认证

```python
# authentication/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from django.core.mail import send_mail
import secrets
import random

@api_view(['POST'])
def request_magic_link(request):
    email = request.data.get('email')
    
    # 生成 token 和 OTP
    magic_token = secrets.token_urlsafe(32)
    otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # 存储到 Redis (10分钟过期)
    cache.set(f'magic_token:{magic_token}', email, timeout=600)
    cache.set(f'otp:{email}', otp_code, timeout=600)
    
    # 发送邮件
    magic_link = f"https://yourdomain.com/auth/verify?token={magic_token}"
    send_mail(
        'Login to BIOTech Futures Hub',
        f'Click: {magic_link}\nOr enter code: {otp_code}',
        'noreply@biotechfutures.org',
        [email],
    )
    
    return Response({'success': True, 'message': 'Magic link sent'})

@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    code = request.data.get('code')
    
    cached_code = cache.get(f'otp:{email}')
    if cached_code != code:
        return Response({'error': 'Invalid code'}, status=400)
    
    # 获取或创建用户
    user, created = User.objects.get_or_create(email=email, defaults={'username': email})
    
    # 生成 JWT
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'role': user.role,
            'track': user.track,
        }
    })
```

### 2.3 URL 配置

```python
# authentication/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('magic-link', views.request_magic_link),
    path('verify-otp', views.verify_otp),
    path('refresh', views.refresh_token),  # 使用 simplejwt 自带的
]
```

**✅ Step 2 完成标准：**
- 前端能发送邮箱请求 magic link
- 能收到邮件（包含 link 和 OTP）
- 验证 OTP 后能获得 JWT token
- 使用 token 能访问受保护的 API

---

## Step 3: 用户管理与个人资料

### 3.1 用户 API

```python
# users/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import User, UserProfile
from .serializers import UserSerializer, UserProfileSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """更新个人资料"""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data.get('profile'), partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True})
```

### 3.2 Serializers

```python
# users/serializers.py

from rest_framework import serializers
from .models import User, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'track', 'status', 'profile']
```

**✅ Step 3 完成标准：**
- GET /api/users/me 返回当前用户信息
- PUT /api/users/me 能更新个人资料
- 前端个人资料页能显示和编辑

---

## Step 4: 群组管理与任务系统

### 4.1 群组模型

```python
# groups/models.py

from django.db import models
from users.models import User

class Group(models.Model):
    id = models.CharField(max_length=50, primary_key=True)  # BTF046
    name = models.CharField(max_length=255)
    track = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default='active')
    mentor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='mentored_groups')
    created_at = models.DateTimeField(auto_now_add=True)

class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # mentor, student
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('group', 'user')

class Milestone(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField(default=0)

class Task(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 4.2 群组 API

```python
# groups/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Group, Task

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    
    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """获取我的群组"""
        groups = Group.objects.filter(members__user=request.user)
        serializer = self.get_serializer(groups, many=True)
        return Response({'groups': serializer.data})
    
    @action(detail=True, methods=['post'], url_path='milestones/(?P<milestone_id>[^/.]+)/tasks')
    def add_task(self, request, pk=None, milestone_id=None):
        """添加任务"""
        task = Task.objects.create(
            milestone_id=milestone_id,
            name=request.data.get('name'),
            completed=False
        )
        return Response(TaskSerializer(task).data, status=201)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    
    def update(self, request, *args, **kwargs):
        """更新任务状态"""
        task = self.get_object()
        task.completed = request.data.get('completed', task.completed)
        task.save()
        return Response({'success': True, 'task': TaskSerializer(task).data})
```

**✅ Step 4 完成标准：**
- GET /api/groups/my-groups 返回用户群组
- GET /api/groups/{id} 返回群组详情（成员+任务）
- PUT /api/groups/{id}/tasks/{taskId} 能更新任务状态
- POST /api/groups/{id}/milestones/{mid}/tasks 能添加任务

---

## Step 5: 聊天消息系统

### 5.1 消息模型

```python
# chat/models.py

from django.db import models
from users.models import User
from groups.models import Group

class Message(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file_url = models.URLField()
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)
```

### 5.2 消息 API

```python
# chat/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Message

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    
    def list(self, request, group_id):
        """获取群组消息"""
        messages = Message.objects.filter(group_id=group_id).order_by('-created_at')[:50]
        return Response({
            'messages': MessageSerializer(messages, many=True).data,
            'hasMore': False
        })
    
    def create(self, request, group_id):
        """发送消息"""
        message = Message.objects.create(
            group_id=group_id,
            author=request.user,
            text=request.data.get('text')
        )
        return Response(MessageSerializer(message).data, status=201)
```

### 5.3 文件上传

```python
# core/views.py

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.core.files.storage import default_storage

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request):
    """上传文件到 Vultr Object Storage"""
    file = request.FILES.get('file')
    
    # 保存文件（自动上传到 S3）
    file_path = default_storage.save(f'uploads/{file.name}', file)
    file_url = default_storage.url(file_path)
    
    return Response({
        'url': file_url,
        'filename': file.name,
        'size': file.size
    }, status=201)
```

### 5.4 URL 配置

```python
# chat/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('groups/<str:group_id>/messages', views.MessageViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
]

# core/urls.py
urlpatterns = [
    path('uploads', views.upload_file),
]
```

**✅ Step 5 完成标准：**
- GET /api/groups/{id}/messages 返回消息列表
- POST /api/groups/{id}/messages 能发送消息
- POST /api/uploads 能上传文件到 Vultr Object Storage
- 前端聊天功能可用

---

## Step 6: 资源库管理

### 6.1 资源模型

```python
# resources/models.py

from django.db import models

class Resource(models.Model):
    TYPE_CHOICES = [
        ('document', 'Document'),
        ('video', 'Video'),
        ('template', 'Template'),
        ('guide', 'Guide'),
    ]
    
    ROLE_CHOICES = [
        ('all', 'All Users'),
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('supervisor', 'Supervisor'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    file_url = models.URLField()
    cover_image = models.URLField(blank=True, null=True)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 6.2 资源 API

```python
# resources/views.py

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Resource

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'role']
    search_fields = ['title', 'description']
    
    def list(self, request):
        """列表展示，支持筛选"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # 根据用户角色过滤
        user_role = request.user.role
        queryset = queryset.filter(role__in=['all', user_role])
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['put'])
    def update_cover(self, request, pk=None):
        """更新封面（仅管理员）"""
        resource = self.get_object()
        file = request.FILES.get('coverImage')
        
        # 上传到 S3
        file_path = default_storage.save(f'covers/{file.name}', file)
        resource.cover_image = default_storage.url(file_path)
        resource.save()
        
        return Response({'coverImage': resource.cover_image})
```

**✅ Step 6 完成标准：**
- GET /api/resources 返回资源列表（支持筛选）
- GET /api/resources/{id} 返回资源详情
- POST /api/resources 能上传资源（Admin）
- PUT /api/resources/{id}/cover 能更新封面（Admin）

---

## Step 7: 活动管理

### 7.1 活动模型

```python
# events/models.py

from django.db import models
from users.models import User

class Event(models.Model):
    TYPE_CHOICES = [
        ('in-person', 'In Person'),
        ('virtual', 'Virtual'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    date = models.DateField()
    time = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    cover_image = models.URLField(blank=True, null=True)
    register_link = models.URLField(blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'user')
```

### 7.2 活动 API

```python
# events/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Event, EventRegistration

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    
    def list(self, request):
        """活动列表"""
        queryset = self.get_queryset()
        
        # 筛选类型
        event_type = request.query_params.get('type')
        if event_type:
            queryset = queryset.filter(type=event_type)
        
        # 只显示未来的活动
        if request.query_params.get('upcoming'):
            from datetime import date
            queryset = queryset.filter(date__gte=date.today())
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """报名活动"""
        event = self.get_object()
        
        registration, created = EventRegistration.objects.get_or_create(
            event=event,
            user=request.user
        )
        
        if created:
            return Response({'success': True, 'message': 'Successfully registered'})
        else:
            return Response({'success': False, 'message': 'Already registered'}, status=400)
```

**✅ Step 7 完成标准：**
- GET /api/events 返回活动列表
- GET /api/events/{id} 返回活动详情
- POST /api/events/{id}/register 能报名活动
- PUT /api/events/{id}/cover 能更新封面（Admin）

---

## Step 8: 公告系统

### 8.1 公告模型

```python
# announcements/models.py

from django.db import models

class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    ]
    
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField()
    author = models.CharField(max_length=100, default='Program Team')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)
```

### 8.2 公告 API

```python
# announcements/views.py

from rest_framework import viewsets
from .models import Announcement

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    
    def list(self, request):
        """公告列表"""
        queryset = self.get_queryset()
        
        # 根据受众筛选
        user_role = request.user.role
        queryset = queryset.filter(audience__in=['all', user_role])
        
        # 搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        queryset = queryset.order_by('-date')
        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})
```

**✅ Step 8 完成标准：**
- GET /api/announcements 返回公告列表（按角色过滤）
- GET /api/announcements/{id} 返回公告详情
- POST /api/announcements 能创建公告（Admin）

---

## Step 9: 管理员面板

### 9.1 统计 API

```python
# users/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count

@api_view(['GET'])
def admin_stats(request):
    """管理员统计数据"""
    track = request.query_params.get('track')
    
    users_qs = User.objects.all()
    if track and track != 'Global':
        users_qs = users_qs.filter(track=track)
    
    stats = {
        'totalUsers': users_qs.count(),
        'activeGroups': Group.objects.filter(status='active').count(),
        'mentors': {
            'total': users_qs.filter(role='mentor').count(),
            'active': users_qs.filter(role='mentor', status='active').count(),
        },
        'students': {
            'total': users_qs.filter(role='student').count(),
        },
    }
    
    return Response(stats)
```

### 9.2 用户管理 API

```python
# users/views.py (继续)

class AdminUserViewSet(viewsets.ModelViewSet):
    """管理员用户管理"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """用户列表"""
        queryset = self.get_queryset()
        
        # 筛选
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        track = request.query_params.get('track')
        if track and track != 'Global':
            queryset = queryset.filter(track=track)
        
        # 搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search)
            )
        
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        """更新用户状态"""
        user = self.get_object()
        user.status = request.data.get('status')
        user.save()
        return Response({'success': True, 'user': UserSerializer(user).data})
```

**✅ Step 9 完成标准：**
- GET /api/admin/stats 返回统计数据
- GET /api/admin/users 返回用户列表（支持筛选）
- PUT /api/admin/users/{id}/status 能更新用户状态

---

## Step 10: 主 URL 配置与测试

### 10.1 主 urls.py

```python
# btf_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth
    path('api/auth/', include('authentication.urls')),
    path('api/auth/refresh', TokenRefreshView.as_view()),
    
    # Users
    path('api/users/', include('users.urls')),
    path('api/admin/', include('users.admin_urls')),
    
    # Groups
    path('api/groups/', include('groups.urls')),
    
    # Chat
    path('api/', include('chat.urls')),
    
    # Resources
    path('api/resources/', include('resources.urls')),
    
    # Events
    path('api/events/', include('events.urls')),
    
    # Announcements
    path('api/announcements/', include('announcements.urls')),
    
    # Core (uploads)
    path('api/', include('core.urls')),
]
```

### 10.2 创建测试数据

```python
# core/management/commands/seed_data.py

from django.core.management.base import BaseCommand
from users.models import User, UserProfile
from groups.models import Group, GroupMember, Milestone, Task

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # 创建测试用户
        admin = User.objects.create_user(
            username='admin',
            email='admin@btf.org',
            password='admin123',
            role='admin'
        )
        
        mentor = User.objects.create_user(
            username='anita',
            email='anita.pickard@email.com',
            password='mentor123',
            role='mentor',
            track='AUS-NSW'
        )
        
        student = User.objects.create_user(
            username='yilin',
            email='yilin.guo@email.com',
            password='student123',
            role='student',
            track='AUS-NSW'
        )
        
        # 创建群组
        group = Group.objects.create(
            id='BTF046',
            name='BTF046',
            track='AUS-NSW',
            mentor=mentor
        )
        
        GroupMember.objects.create(group=group, user=mentor, role='mentor')
        GroupMember.objects.create(group=group, user=student, role='student')
        
        # 创建 Milestone 和 Task
        milestone = Milestone.objects.create(
            group=group,
            title='Getting Started',
            order_index=1
        )
        
        Task.objects.create(
            milestone=milestone,
            name='Determine Group Topic',
            completed=False
        )
        
        self.stdout.write(self.style.SUCCESS('测试数据创建成功！'))
```

运行命令：
```bash
python manage.py seed_data
```

**✅ Step 10 完成标准：**
- 所有 API 端点都能访问
- 使用测试账号能完成完整流程
- 前端能正常调用所有功能

---

## Step 11: Vultr 部署配置

### 11.1 准备 Vultr VPS

```bash
# 1. 创建 Vultr VPS (Ubuntu 22.04)
# 2. SSH 连接到服务器
ssh root@your_vultr_ip

# 3. 更新系统
apt update && apt upgrade -y

# 4. 安装依赖
apt install python3.11 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server -y

# 5. 创建数据库
sudo -u postgres psql
CREATE DATABASE btf_db;
CREATE USER btf_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE btf_db TO btf_user;
\q
```

### 11.2 部署 Django 应用

```bash
# 1. 克隆代码
cd /var/www
git clone your_repo_url btf_backend
cd btf_backend

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
nano .env
# 填入生产环境配置

# 5. 数据库迁移
python manage.py migrate

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 创建超级用户
python manage.py createsuperuser
```

### 11.3 配置 Gunicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 创建 Gunicorn 配置
nano /etc/systemd/system/btf.service
```

```ini
[Unit]
Description=BTF Backend
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/btf_backend
Environment="PATH=/var/www/btf_backend/venv/bin"
ExecStart=/var/www/btf_backend/venv/bin/gunicorn --workers 3 --bind unix:/var/www/btf_backend/btf.sock btf_backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
systemctl start btf
systemctl enable btf
```

### 11.4 配置 Nginx

```bash
nano /etc/nginx/sites-available/btf
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://unix:/var/www/btf_backend/btf.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /var/www/btf_backend/staticfiles/;
    }
}
```

```bash
# 启用配置
ln -s /etc/nginx/sites-available/btf /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 11.5 配置 SSL (Let's Encrypt)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d api.yourdomain.com
```

**✅ Step 11 完成标准：**
- 后端部署到 Vultr VPS
- Nginx 配置正确
- SSL 证书配置成功
- API 通过 https://api.yourdomain.com 可访问

---

## 完整的 requirements.txt

```txt
Django==5.0
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
psycopg2-binary==2.9.9
redis==5.0.0
django-redis==5.4.0
django-storages==1.14.2
boto3==1.34.0
django-anymail==10.2
django-cors-headers==4.3.0
python-dotenv==1.0.0
gunicorn==21.2.0
django-filter==23.5
```

---

## 开发顺序总结

| Step | 功能模块 | 完成标志 |
|------|---------|---------|
| **Step 1** | 项目初始化 | Django 能运行 |
| **Step 2** | 认证系统 | 前端能登录 |
| **Step 3** | 用户管理 | 个人资料可编辑 |
| **Step 4** | 群组管理 | 群组页面功能完整 |
| **Step 5** | 聊天系统 | 能发送消息和文件 |
| **Step 6** | 资源库 | 资源页面可用 |
| **Step 7** | 活动管理 | 活动页面可用 |
| **Step 8** | 公告系统 | 公告页面可用 |
| **Step 9** | 管理面板 | Admin 功能完整 |
| **Step 10** | 集成测试 | 所有功能联调通过 |
| **Step 11** | 部署上线 | 生产环境运行 |

---

## 关键注意事项

### 🎯 优先级排序
1. **Step 2 最重要** - 没有登录，前端无法使用
2. **Step 3-5 次重要** - 核心功能
3. **Step 6-9 可迭代** - 可以先简单实现

### 🔧 开发建议
- 每完成一个 Step 就测试，不要积累问题
- 使用 Django Admin 快速验证数据模型
- 用 Postman 测试 API 端点
- 先让功能跑通，不要纠结细节

### ⚡ 快速上线策略
- Step 1-5 完成后就可以上线基础版本
- Step 6-9 可以后续迭代添加
- 安全加固可以放到 v2.0

---

**预计完成时间：2-3 周**  
**最后更新：** 2025年10月14日