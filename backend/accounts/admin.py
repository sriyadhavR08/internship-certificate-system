from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, StudentProfile

class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'full_name')

class ChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CreationForm
    form = ChangeForm
    ordering = ('email',)
    list_display = ('email', 'full_name', 'role', 'is_active')
    search_fields = ('email', 'full_name')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = ((None, {'fields': ('email', 'password', 'full_name')}), ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}))
    add_fieldsets = ((None, {'fields': ('email', 'full_name', 'password1', 'password2', 'role', 'is_staff')}),)
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(StudentProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'register_number', 'college_name')
    search_fields = ('user__full_name', 'register_number')
    readonly_fields = tuple(f.name for f in StudentProfile._meta.fields)
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
