from django.contrib import admin

from .models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "created_at"]
    list_filter = ["user"]
    search_fields = ["title", "ingredients"]
