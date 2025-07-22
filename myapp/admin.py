from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserInfo

# Inline admin for UserInfo (IP + Country)
class UserInfoInline(admin.StackedInline):
    model = UserInfo
    can_delete = False
    verbose_name_plural = 'User Info'

# Custom UserAdmin to show UserInfo in user list
class CustomUserAdmin(UserAdmin):
    inlines = (UserInfoInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_ip', 'get_country')

    def get_ip(self, obj):
        try:
            return obj.userinfo.ip_address
        except UserInfo.DoesNotExist:
            return '-'
    get_ip.short_description = 'IP Address'

    def get_country(self, obj):
        try:
            return obj.userinfo.country
        except UserInfo.DoesNotExist:
            return '-'
    get_country.short_description = 'Country'

# Replace default User admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
