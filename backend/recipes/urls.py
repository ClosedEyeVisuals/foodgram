from django.urls import path

from .views import ShortUrlRedirectView


urlpatterns = [
    path('s/<slug:short_url>/', ShortUrlRedirectView.as_view()),
]
