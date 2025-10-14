from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """在用户管理页面内嵌显示个人资料"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户管理界面"""
    inlines = (UserProfileInline,)

    list_display = [
        'email',
        'username',
        'role',
        'track',
        'status',
        'is_staff',
        'date_joined'
    ]
    list_filter = ['role', 'track', 'status', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Role & Track', {'fields': ('role', 'track', 'status')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'track'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料管理界面"""
    list_display = [
        'user',
        'school_name',
        'year_level',
        'country',
        'region',
        'created_at'
    ]
    list_filter = ['country', 'region', 'year_level']
    search_fields = ['user__email', 'school_name']
    readonly_fields = ['created_at', 'updated_at']