from django.conf import settings
from django.db import models

from apps.common.ai import get_embedding
from apps.common.embedding_field import EmbeddingField


class Recipe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes"
    )
    title = models.CharField(max_length=255)
    ingredients = models.TextField(help_text="Newline- or comma-separated list of ingredients.")
    instructions = models.TextField()
    embedding = EmbeddingField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def embedding_source_text(self) -> str:
        return f"{self.title}\n{self.ingredients}\n{self.instructions}"

    def compute_embedding(self):
        """Compute and set (but do not save) the embedding for this recipe."""
        self.embedding = get_embedding(self.embedding_source_text())

    def save(self, *args, **kwargs):
        # Recompute the embedding whenever the embedding-relevant content
        # changes (including on first create, where pk is None).
        recompute = kwargs.pop("recompute_embedding", True)
        if recompute:
            self.compute_embedding()
        super().save(*args, **kwargs)
