from django.contrib import admin

from .models import Group, GroupMember, Milestone, Task


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "track", "status", "mentor"]
    search_fields = ["id", "name", "track"]
    list_filter = ["track", "status"]
    inlines = [GroupMemberInline, MilestoneInline]


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ["group", "user", "role", "joined_at"]
    list_filter = ["role"]
    search_fields = ["group__id", "group__name", "user__email"]


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "group", "order_index"]
    list_filter = ["group"]
    search_fields = ["title", "group__id", "group__name"]
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["name", "milestone", "completed", "assigned_to", "due_date"]
    list_filter = ["completed", "milestone__group"]
    search_fields = ["name", "milestone__group__id"]
