from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户模型
    扩展 Django 的默认用户模型，添加角色、赛道等字段
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # 重写 email 字段，设为必填且唯一
    email = models.EmailField(unique=True, blank=False)

    # 自定义字段
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )
    track = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # 使用 email 作为登录标识
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # createsuperuser 时会额外要求的字段

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """返回用户全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email


class UserProfile(models.Model):
    """
    用户个人资料扩展
    存储额外的用户信息
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # 基本信息
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    # 兴趣领域 - 使用 JSONField 存储列表
    areas_of_interest = models.JSONField(default=list, blank=True)

    # 学校信息
    school_name = models.CharField(max_length=255, blank=True)
    year_level = models.IntegerField(null=True, blank=True)

    # 地理位置
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # 其他信息
    availability = models.TextField(blank=True)
    bio = models.TextField(blank=True, help_text='个人简介')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"