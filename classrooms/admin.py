from django.contrib import admin
from .models import Subject, ClassGroup, GroupMembership, Announcement

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher')
    search_fields = ('name', 'teacher__user__username')
    list_filter = ('teacher',)

@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name', 'subject__name')
    list_filter = ('subject',)

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'joined_at')
    list_filter = ('group', 'joined_at')
    search_fields = ('student__user__username', 'group__name')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('title', 'body')
