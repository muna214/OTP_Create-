from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserInfo

class UserInfoInline(admin.StackedInline):
    model = UserInfo
    can_delete = False
    verbose_name_plural = 'User Info'
    readonly_fields = ('ip_address', 'country')  # Optional

class CustomUserAdmin(UserAdmin):
    inlines = (UserInfoInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_ip', 'get_country')
    search_fields = ('username', 'email', 'userinfo__ip_address', 'userinfo__country')  # Optional
    list_filter = ('userinfo__country', 'is_staff', 'is_superuser')  # Optional

    def get_ip(self, obj):
        try:
            return obj.userinfo.ip_address or '-'
        except UserInfo.DoesNotExist:
            return '-'
    get_ip.short_description = 'IP Address'

    def get_country(self, obj):
        try:
            return obj.userinfo.country or '-'
        except UserInfo.DoesNotExist:
            return '-'
    get_country.short_description = 'Country'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
