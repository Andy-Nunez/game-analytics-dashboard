import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "./config";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

function App() {
  const [games, setGames] = useState([]);
  const [loadingGames, setLoadingGames] = useState(false);
  const [error, setError] = useState(null);

  const [appidInput, setAppidInput] = useState("");
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");

  // Filters & sorting
  const [filterGenre, setFilterGenre] = useState("all");
  const [showFreeOnly, setShowFreeOnly] = useState(false);
  const [sortKey, setSortKey] = useState("name");
  const [sortDir, setSortDir] = useState("asc"); // 'asc' | 'desc'

  // ---------------------------------------------------------------------------
  // Fetch games
  // ---------------------------------------------------------------------------
  const fetchGames = async () => {
    try {
      setLoadingGames(true);
      setError(null);
      const res = await fetch(`${API_BASE_URL}/games`);
      if (!res.ok) {
        throw new Error(`Error fetching games: ${res.status}`);
      }
      const data = await res.json();
      setGames(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to load games");
    } finally {
      setLoadingGames(false);
    }
  };

  useEffect(() => {
    fetchGames();
  }, []);

  // ---------------------------------------------------------------------------
  // Sync a game from Steam by appid
  // ---------------------------------------------------------------------------
  const handleSync = async (e) => {
    e.preventDefault();
    setSyncMessage("");
    setError(null);

    const trimmed = appidInput.trim();
    if (!trimmed || isNaN(Number(trimmed))) {
      setError("Please enter a valid numeric Steam appid.");
      return;
    }

    try {
      setSyncLoading(true);
      const res = await fetch(
        `${API_BASE_URL}/games/sync-steam/${trimmed}`,
        {
          method: "POST",
        }
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Sync failed with status ${res.status}`);
      }

      const game = await res.json();
      setSyncMessage(`Synced "${game.name}" (appid: ${game.steam_appid}).`);
      setAppidInput("");

      // Refresh list
      fetchGames();
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to sync game");
    } finally {
      setSyncLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Helpers to extract genres, etc.
  // ---------------------------------------------------------------------------
  const getPrimaryGenre = (game) => {
    if (!game.genre) return null;
    // we stored as comma-separated string from Steam
    return game.genre.split(",")[0]?.trim() || null;
  };

  const allGenres = useMemo(() => {
    const set = new Set();
    games.forEach((g) => {
      const primary = getPrimaryGenre(g);
      if (primary) set.add(primary);
    });
    return Array.from(set).sort();
  }, [games]);

  // ---------------------------------------------------------------------------
  // Filter + sort games for table & charts
  // ---------------------------------------------------------------------------
  const displayGames = useMemo(() => {
    let filtered = [...games];

    if (filterGenre !== "all") {
      filtered = filtered.filter((g) => getPrimaryGenre(g) === filterGenre);
    }

    if (showFreeOnly) {
      filtered = filtered.filter((g) => g.is_free === true);
    }

    filtered.sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];

      if (sortKey === "name") {
        av = av || "";
        bv = bv || "";
        const cmp = av.localeCompare(bv);
        return sortDir === "asc" ? cmp : -cmp;
      }

      // numeric sort for metacritic_score, recommendations_count, steam_appid
      av = av ?? -Infinity;
      bv = bv ?? -Infinity;

      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [games, filterGenre, showFreeOnly, sortKey, sortDir]);

  // ---------------------------------------------------------------------------
  // Chart data: genre distribution & free vs paid
  // ---------------------------------------------------------------------------
  const genreChartData = useMemo(() => {
    const counts = new Map();
    displayGames.forEach((g) => {
      const primary = getPrimaryGenre(g) || "Unknown";
      counts.set(primary, (counts.get(primary) || 0) + 1);
    });
    return Array.from(counts.entries()).map(([genre, count]) => ({
      genre,
      count,
    }));
  }, [displayGames]);

  const freePaidChartData = useMemo(() => {
    let freeCount = 0;
    let paidCount = 0;

    displayGames.forEach((g) => {
      if (g.is_free) freeCount += 1;
      else paidCount += 1;
    });

    return [
      { name: "Free", value: freeCount },
      { name: "Paid", value: paidCount },
    ];
  }, [displayGames]);

  const freePaidColors = ["#4caf50", "#f44336"];

  // ---------------------------------------------------------------------------
  // UI
  // ---------------------------------------------------------------------------
  return (
    <div
      style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "2rem",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <h1 style={{ marginBottom: "0.5rem" }}>Steam Games Dashboard</h1>
      <p style={{ marginBottom: "1.5rem", color: "#555" }}>
        Backend: FastAPI + PostgreSQL · Data: Steam Storefront API
      </p>

      {/* Sync form */}
      <form
        onSubmit={handleSync}
        style={{
          display: "flex",
          gap: "0.5rem",
          marginBottom: "1.5rem",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <label>
          Steam appid:{" "}
          <input
            type="text"
            value={appidInput}
            onChange={(e) => setAppidInput(e.target.value)}
            placeholder="e.g. 620 for Portal 2"
            style={{ padding: "0.4rem 0.6rem" }}
          />
        </label>
        <button
          type="submit"
          disabled={syncLoading}
          style={{
            padding: "0.45rem 0.9rem",
            cursor: syncLoading ? "wait" : "pointer",
          }}
        >
          {syncLoading ? "Syncing..." : "Sync from Steam"}
        </button>
      </form>

      {syncMessage && (
        <div style={{ marginBottom: "1rem", color: "green" }}>
          {syncMessage}
        </div>
      )}

      {error && (
        <div style={{ marginBottom: "1rem", color: "red" }}>
          {error}
        </div>
      )}

      {/* Filters & sorting */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #eee",
          borderRadius: "8px",
        }}
      >
        <h2 style={{ marginBottom: "0.75rem" }}>Filters & Sorting</h2>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "1rem",
            alignItems: "center",
          }}
        >
          {/* Genre filter */}
          <label>
            Genre:{" "}
            <select
              value={filterGenre}
              onChange={(e) => setFilterGenre(e.target.value)}
            >
              <option value="all">All</option>
              {allGenres.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </label>

          {/* Free only */}
          <label>
            <input
              type="checkbox"
              checked={showFreeOnly}
              onChange={(e) => setShowFreeOnly(e.target.checked)}
              style={{ marginRight: "0.3rem" }}
            />
            Free games only
          </label>

          {/* Sort key */}
          <label>
            Sort by:{" "}
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value)}
            >
              <option value="name">Name</option>
              <option value="metacritic_score">Metacritic</option>
              <option value="recommendations_count">Recommendations</option>
              <option value="steam_appid">AppID</option>
            </select>
          </label>

          {/* Sort direction */}
          <label>
            Direction:{" "}
            <select
              value={sortDir}
              onChange={(e) => setSortDir(e.target.value)}
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </label>
        </div>
      </section>

      {/* Charts */}
      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ marginBottom: "0.75rem" }}>Overview</h2>

        {displayGames.length === 0 ? (
          <p>No games to chart yet. Try syncing some appids.</p>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1fr)",
              gap: "1.5rem",
              alignItems: "stretch",
            }}
          >
            {/* Genre distribution */}
            <div
              style={{
                border: "1px solid #eee",
                borderRadius: "8px",
                padding: "1rem",
                minHeight: "260px",
              }}
            >
              <h3 style={{ marginBottom: "0.5rem" }}>
                Games by Primary Genre
              </h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={genreChartData}>
                  <XAxis dataKey="genre" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Free vs Paid */}
            <div
              style={{
                border: "1px solid #eee",
                borderRadius: "8px",
                padding: "1rem",
                minHeight: "260px",
              }}
            >
              <h3 style={{ marginBottom: "0.5rem" }}>Free vs Paid</h3>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={freePaidChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    label
                  >
                    {freePaidChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={freePaidColors[index % freePaidColors.length]}
                      />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </section>

      {/* Games table */}
      <section>
        <h2 style={{ marginBottom: "0.75rem" }}>Games in Database</h2>
        {loadingGames ? (
          <p>Loading games...</p>
        ) : displayGames.length === 0 ? (
          <p>No games match the current filters.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.9rem",
              }}
            >
              <thead>
                <tr>
                  <th style={thStyle}>ID</th>
                  <th style={thStyle}>Name</th>
                  <th style={thStyle}>AppID</th>
                  <th style={thStyle}>Genre</th>
                  <th style={thStyle}>Developer</th>
                  <th style={thStyle}>Publisher</th>
                  <th style={thStyle}>Release Date</th>
                  <th style={thStyle}>Free?</th>
                  <th style={thStyle}>Metacritic</th>
                  <th style={thStyle}>Recs</th>
                  <th style={thStyle}>Languages</th>
                  <th style={thStyle}>Categories</th>
                </tr>
              </thead>
              <tbody>
                {displayGames.map((g) => (
                  <tr key={g.id}>
                    <td style={tdStyle}>{g.id}</td>
                    <td style={tdStyle}>{g.name}</td>
                    <td style={tdStyle}>{g.steam_appid}</td>
                    <td style={tdStyle}>{g.genre}</td>
                    <td style={tdStyle}>{g.developer}</td>
                    <td style={tdStyle}>{g.publisher}</td>
                    <td style={tdStyle}>{g.release_date ?? "—"}</td>
                    <td style={tdStyle}>{g.is_free ? "Yes" : "No"}</td>
                    <td style={tdStyle}>{g.metacritic_score ?? "—"}</td>
                    <td style={tdStyle}>{g.recommendations_count ?? "—"}</td>
                    <td style={tdStyle}>{g.languages ?? "—"}</td>
                    <td style={tdStyle}>{g.categories ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

const thStyle = {
  textAlign: "left",
  padding: "0.4rem 0.6rem",
  borderBottom: "1px solid #ddd",
  backgroundColor: "#f7f7f7",
};

const tdStyle = {
  padding: "0.4rem 0.6rem",
  borderBottom: "1px solid #eee",
};

export default App;
