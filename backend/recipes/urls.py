from django.urls import path

from .views import ShortUrlRedirectView


urlpatterns = [
    path('<slug:short_url>/', ShortUrlRedirectView.as_view()),
]
