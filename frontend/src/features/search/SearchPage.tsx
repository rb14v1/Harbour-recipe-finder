import React, { useState } from "react";
import { searchRecipes } from "../../api/recipes";
import type { SearchResponse } from "../../types";

const STUB_MARKER = "[STUB AI RESPONSE";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const data = await searchRecipes(query);
      setResult(data);
    } catch {
      setError("Search failed.");
    } finally {
      setLoading(false);
    }
  }

  const isStub = result?.suggestion.includes(STUB_MARKER);

  return (
    <div>
      <h1>Search Recipes</h1>
      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          placeholder="e.g. I have chicken and broccoli"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="search-results">
          {isStub && (
            <p className="stub-note">
              Running in stub mode: no OPENAI_API_KEY configured on the server, so this
              suggestion and the search embeddings are deterministic placeholders, not real AI
              output.
            </p>
          )}

          <h2>Suggestion</h2>
          <p className="suggestion">{result.suggestion}</p>

          <h2>Matching Recipes</h2>
          {result.matches.length === 0 && <p>No matches found.</p>}
          <ul className="match-list">
            {result.matches.map((m) => (
              <li key={m.recipe_id}>
                <span className="match-title">{m.title}</span>
                <span className="match-score">score: {m.score.toFixed(4)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
