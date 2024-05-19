from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
    UserSubscriptionsViewSet,
    PasswordResetViewSet
)

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('users', UserSubscriptionsViewSet, basename='users')
router.register('reset_password', PasswordResetViewSet, basename='reset_password')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
