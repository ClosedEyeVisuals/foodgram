from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from users.constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
                             MAX_LAST_NAME_LENGTH, MAX_USERNAME_LENGTH)


class User(AbstractUser):
    """Модель пользователя."""
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name='E-mail'
    )
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        help_text=f'Максимальное кол-во символов: {MAX_USERNAME_LENGTH}.',
        validators=[
            UnicodeUsernameValidator()
        ],
        error_messages={
            "unique": "Пользователь с таким никнеймом уже существует!"},
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки одного пользователя на другого."""
    user = models.ForeignKey(
        User,
        related_name='follows',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    following = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE,
        verbose_name='Подписан на'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='check_self_following'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user__username', 'following__username')

    def __str__(self):
        return f'{self.user} - {self.following}'
