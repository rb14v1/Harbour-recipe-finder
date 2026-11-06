import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createRecipe, getRecipe, updateRecipe } from "../../api/recipes";

export default function RecipeFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [instructions, setInstructions] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isEdit) {
      getRecipe(Number(id)).then((r) => {
        setTitle(r.title);
        setIngredients(r.ingredients);
        setInstructions(r.instructions);
      });
    }
  }, [id, isEdit]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = { title, ingredients, instructions };
      if (isEdit) {
        await updateRecipe(Number(id), payload);
      } else {
        await createRecipe(payload);
      }
      navigate("/recipes");
    } catch {
      setError("Failed to save recipe.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>{isEdit ? "Edit Recipe" : "Add Recipe"}</h1>
      <form onSubmit={handleSubmit} className="recipe-form">
        <label>
          Title
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Ingredients (one per line or comma-separated)
          <textarea
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
            rows={6}
            required
          />
        </label>
        <label>
          Instructions
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            rows={8}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Save Recipe"}
        </button>
      </form>
    </div>
  );
}
