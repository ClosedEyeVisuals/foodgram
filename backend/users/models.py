from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from recipes.constants import (MAX_EMAIL_LENGTH, MAX_FIRST_NAME_LENGTH,
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
        help_text='Максимальное кол-во символов: 150.',
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

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки одного пользователя на другого."""
    user = models.ForeignKey(User, related_name='follows',
                             on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers',
                                  on_delete=models.CASCADE)

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
        ordering = ('-id',)

    def __str__(self):
        return f'{self.user} - {self.following}'
