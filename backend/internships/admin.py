from django.contrib import admin
from .models import Internship

@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('student', 'project_name', 'start_date', 'end_date', 'status')
    search_fields = ('student__full_name', 'project_name')
    list_filter = ('status',)
    readonly_fields = tuple(f.name for f in Internship._meta.fields)
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
