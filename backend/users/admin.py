from django.contrib import admin

from .models import Follow, User


class UserAdmin(admin.ModelAdmin):
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


class FollowAdmin(admin.ModelAdmin):
    search_fields = (
        'user__username',
        'following__username'
    )


admin.site.register(Follow, FollowAdmin)
admin.site.register(User, UserAdmin)
