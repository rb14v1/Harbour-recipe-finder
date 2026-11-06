from rest_framework import serializers

from .models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "title", "ingredients", "instructions", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=False)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=50)


class SearchMatchSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()
    title = serializers.CharField()
    score = serializers.FloatField()


class SearchResponseSerializer(serializers.Serializer):
    matches = SearchMatchSerializer(many=True)
    suggestion = serializers.CharField()
