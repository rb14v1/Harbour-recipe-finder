from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.ai import generate_answer, get_embedding
from apps.common.vector_search import similarity_search

from .models import Recipe
from .serializers import (
    RecipeSerializer,
    SearchRequestSerializer,
    SearchResponseSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Scoped strictly to the requesting user -- never exposes other
        # users' recipes, including via the search endpoint below.
        return Recipe.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SearchView(APIView):
    """
    POST {"query": "...", "top_k": 5}

    Embeds the query, runs similarity search over the requesting user's own
    recipes only, and asks the AI layer for a grounded suggestion based on
    the top matches.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request_serializer = SearchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        query = request_serializer.validated_data["query"]
        top_k = request_serializer.validated_data.get(
            "top_k", getattr(settings, "SEARCH_TOP_K_DEFAULT", 5)
        )

        query_vector = get_embedding(query)

        queryset = Recipe.objects.filter(user=request.user)
        top_matches = similarity_search(queryset, query_vector, top_k=top_k)

        matches = [
            {
                "recipe_id": recipe.id,
                "title": recipe.title,
                "score": recipe.similarity_score,
            }
            for recipe in top_matches
        ]

        context_snippets = [f"{r.title}: {r.ingredients}" for r in top_matches]
        suggestion = generate_answer(query, context_snippets)

        response_serializer = SearchResponseSerializer(
            {"matches": matches, "suggestion": suggestion}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)
