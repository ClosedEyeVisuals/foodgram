from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group

from users.models import Follow

User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    search_fields = (
        'username',
        'email'
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    search_fields = (
        'user__username',
        'following__username'
    )


admin.site.unregister(Group)
