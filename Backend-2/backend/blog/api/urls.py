from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    RecipeViewset, TagViewset, BaseUserViewset, IngridientViewset)

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('tags', TagViewset, basename='tags')
router_v1.register('ingredients', IngridientViewset, basename='ingredients')
router_v1.register('users', BaseUserViewset, basename='users')
router_v1.register('recipes', RecipeViewset, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
