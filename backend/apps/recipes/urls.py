from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, SearchView

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")

urlpatterns = [
    path("search/", SearchView.as_view(), name="recipe-search"),
    path("", include(router.urls)),
]
