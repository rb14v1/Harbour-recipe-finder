import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteRecipe, listRecipes } from "../../api/recipes";
import type { Recipe } from "../../types";

export default function RecipeListPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    listRecipes()
      .then(setRecipes)
      .catch(() => setError("Failed to load recipes."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleDelete(id: number) {
    if (!confirm("Delete this recipe?")) return;
    await deleteRecipe(id);
    load();
  }

  if (loading) return <p>Loading recipes...</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div>
      <h1>My Recipes</h1>
      {recipes.length === 0 && (
        <p>
          No recipes yet. <Link to="/recipes/new">Add your first one</Link>.
        </p>
      )}
      <ul className="recipe-list">
        {recipes.map((r) => (
          <li key={r.id} className="recipe-card">
            <h2>{r.title}</h2>
            <p className="label">Ingredients</p>
            <pre>{r.ingredients}</pre>
            <p className="label">Instructions</p>
            <pre>{r.instructions}</pre>
            <div className="recipe-actions">
              <Link to={`/recipes/${r.id}/edit`}>Edit</Link>
              <button onClick={() => handleDelete(r.id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
