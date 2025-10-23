from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    controlled_interests = models.JSONField(default=list, blank=True)

    # 学校信息
    school_name = models.CharField(max_length=255, blank=True)
    year_level = models.IntegerField(null=True, blank=True)

    guardian_email = models.EmailField(blank=True)
    supervisor_email = models.EmailField(blank=True)

    # 地理位置
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # 其他信息
    availability = models.TextField(blank=True)
    bio = models.TextField(blank=True, help_text='个人简介')
    join_permission_granted = models.BooleanField(default=False)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"


class SupervisorProfile(models.Model):
    """
    Stores compliance and organisation details for supervisors/mentors.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="supervisor_profile",
    )
    organisation = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    wwcc_number = models.CharField(max_length=100, blank=True)
    wwcc_expiry = models.DateField(null=True, blank=True)
    wwcc_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "supervisor_profiles"
        verbose_name = "Supervisor Profile"
        verbose_name_plural = "Supervisor Profiles"

    def __str__(self) -> str:
        return f"Supervisor profile for {self.user.email}"


class StudentSupervisor(models.Model):
    """
    Junction table linking students with their supervisors/guardians.
    """

    RELATIONSHIP_SUPERVISOR = "supervisor"
    RELATIONSHIP_GUARDIAN = "guardian"
    RELATIONSHIP_MENTOR = "mentor"
    RELATIONSHIP_CHOICES = [
        (RELATIONSHIP_SUPERVISOR, "Supervisor"),
        (RELATIONSHIP_GUARDIAN, "Guardian"),
        (RELATIONSHIP_MENTOR, "Mentor"),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="supervisor_links",
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="supervisee_links",
    )
    relationship_type = models.CharField(
        max_length=32,
        choices=RELATIONSHIP_CHOICES,
        default=RELATIONSHIP_SUPERVISOR,
    )
    join_permission_granted = models.BooleanField(default=False)
    join_permission_granted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_supervisors"
        verbose_name = "Student Supervisor Relationship"
        verbose_name_plural = "Student Supervisor Relationships"
        unique_together = ("student", "supervisor", "relationship_type")
        indexes = [
            models.Index(fields=["student", "relationship_type"]),
            models.Index(fields=["supervisor"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.email} ↔ {self.supervisor.email} ({self.relationship_type})"

    def set_join_permission(self, granted: bool) -> None:
        """
        Toggle the join permission flag and track when it was last granted.
        """

        granted = bool(granted)
        if granted and not self.join_permission_granted:
            self.join_permission_granted_at = timezone.now()
        elif not granted:
            self.join_permission_granted_at = None
        self.join_permission_granted = granted
