from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'issue_date', 'status')
    search_fields = ('certificate_id', 'internship__student__full_name')
    list_filter = ('status',)
    readonly_fields = tuple(f.name for f in Certificate._meta.fields)
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
