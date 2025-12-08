from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Subject)
admin.site.register(ClassGroup)
admin.site.register(GroupMembership)
admin.site.register(Announcement)