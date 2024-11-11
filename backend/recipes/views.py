from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin

from recipes.models import Recipe


class ShortUrlRedirectView(SingleObjectMixin, RedirectView):
    queryset = Recipe.objects.all()

    def get_object(self, queryset=None):
        return get_object_or_404(Recipe, short_url=self.kwargs['short_url'])

    def get_redirect_url(self, *args, **kwargs):
        recipe = self.get_object()
        return f'/api/recipes/{recipe.id}/'
