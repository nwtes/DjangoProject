from django.contrib import admin
from . import models

@admin.register(models.DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'sent_at', 'read')
    list_filter = ('read', 'sent_at')
    search_fields = ('sender__username', 'recipient__username', 'body')
    ordering = ('-sent_at',)
