# “””
Seattle Storm Analytics - Data Collection Pipeline

Pulls WNBA data from multiple public sources:

1. nba_api             –> team stats, player stats, shot chart, lineups, game log
1. sportsdataverse     –> play-by-play, box scores, schedules (ESPN/pre-built Parquet)
1. Basketball-Reference –> historical season stats (scraping)

Requirements:
pip install nba_api pandas sportsdataverse basketball_reference_web_scraper
pip install matplotlib seaborn plotly  # for visualization later

Usage:
python storm_data_pipeline.py
All outputs saved to ./data/ folder as CSV files.
“””

import pandas as pd
import time
import os
from datetime import datetime

# ── nba_api (required for Section 1) ─────────────────────────────────────────

try:
from nba_api.stats.endpoints import (
LeagueDashTeamStats,
LeagueDashPlayerStats,
LeagueDashLineups,
ShotChartDetail,
TeamGameLogs,
)
NBA_API_AVAILABLE = True
except ImportError:
NBA_API_AVAILABLE = False
print(“nba_api not installed. Run: pip install nba_api”)

# ── Optional: sportsdataverse (install separately) ───────────────────────────

try:
from sportsdataverse.wnba import (
load_wnba_team_boxscore,
load_wnba_player_boxscore,
load_wnba_pbp,
load_wnba_schedule,
)
SDV_AVAILABLE = True
except ImportError:
SDV_AVAILABLE = False
print(“sportsdataverse not installed. Run: pip install sportsdataverse”)

# ── Optional: basketball_reference_web_scraper ────────────────────────────────

try:
from basketball_reference_web_scraper import client as bref
BREF_AVAILABLE = True
except ImportError:
BREF_AVAILABLE = False
print(“basketball_reference_web_scraper not installed. Run: pip install basketball_reference_web_scraper”)

# ─────────────────────────────────────────────────────────────────────────────

# CONFIG

# ─────────────────────────────────────────────────────────────────────────────

SEATTLE_STORM_TEAM_ID = “1611661328”   # WNBA Stats API team ID for Seattle Storm

# STATS_SEASON: the season pulled for individual player stats and shot charts.

# TEAM_SEASON:  the season pulled for all TEAM-specific data (lineup combos,

# team ratings, game log). Must reflect a season the current group actually

# played together. Locked to 2025 — the 2026 roster has no shared history yet.

# ROSTER_SEASON: labels output files to reflect the current 2026 roster.

# Note: rookies (Fam, Johnson) have no WNBA history — skipped automatically.

STATS_SEASON         = 2025
TEAM_SEASON          = 2025  # ← locked: 2026 roster has not played together yet
ROSTER_SEASON        = 2026
CURRENT_SEASON       = STATS_SEASON    # alias used by player-level fetch functions
OUTPUT_DIR           = “./data”

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────

# HELPERS

# ─────────────────────────────────────────────────────────────────────────────

def nba_api_request(endpoint_cls, **kwargs) -> pd.DataFrame | None:
“””
Generic nba_api request wrapper.
Each caller is responsible for passing the correct league_id param
(league_id_nullable=“10” for LeagueDash* endpoints, league_id_nullable=“10”
for TeamGameLogs). timeout=60 is injected automatically.
nba_api handles session management, headers, and rate limiting internally.
“””
try:
obj = endpoint_cls(timeout=60, **kwargs)
return obj.get_data_frames()[0]
except Exception as e:
print(f”  ✗ {endpoint_cls.**name**} failed: {e}”)
return None

def save(df: pd.DataFrame, name: str):
path = os.path.join(OUTPUT_DIR, f”{name}.csv”)
df.to_csv(path, index=False)
print(f”  ✓ Saved {len(df)} rows → {path}”)

# ─────────────────────────────────────────────────────────────────────────────

# 1. nba_api  — Team & Player Stats via WNBA Stats API

# Player-level pulls use STATS_SEASON (2025).

# Team-level pulls (lineups, team ratings, game log) use TEAM_SEASON (2025).

# Both are currently 2025 — kept separate so they can diverge independently.

# ─────────────────────────────────────────────────────────────────────────────

def fetch_team_stats(season: int = TEAM_SEASON) -> pd.DataFrame | None:
“”“League-wide team stats — per-game base metrics. Uses TEAM_SEASON.”””
print(”\n[1a] Fetching team stats via nba_api…”)
if not NBA_API_AVAILABLE:
print(”  ✗ nba_api not installed.”)
return None
df = nba_api_request(
LeagueDashTeamStats,
league_id_nullable=“10”,
season=str(season),
season_type_all_star=“Regular Season”,
per_mode_detailed=“PerGame”,
measure_type_detailed_defense=“Base”,
)
if df is not None:
save(df, f”team_stats_{season}”)
return df

def fetch_advanced_team_stats(season: int = TEAM_SEASON) -> pd.DataFrame | None:
“”“Advanced team metrics: OffRtg, DefRtg, NetRtg, Pace, TS%. Uses TEAM_SEASON.”””
print(”\n[1b] Fetching advanced team stats via nba_api…”)
if not NBA_API_AVAILABLE:
print(”  ✗ nba_api not installed.”)
return None
df = nba_api_request(
LeagueDashTeamStats,
league_id_nullable=“10”,
season=str(season),
season_type_all_star=“Regular Season”,
per_mode_detailed=“PerGame”,
measure_type_detailed_defense=“Advanced”,
)
if df is not None:
save(df, f”advanced_team_stats_{season}”)
return df

def fetch_player_stats(season: int = CURRENT_SEASON) -> pd.DataFrame | None:
“”“League-wide player stats — per-game base metrics.”””
print(”\n[1c] Fetching player stats via nba_api…”)
if not NBA_API_AVAILABLE:
print(”  ✗ nba_api not installed.”)
return None
df = nba_api_request(
LeagueDashPlayerStats,
league_id_nullable=“10”,
season=str(season),
season_type_all_star=“Regular Season”,
per_mode_detailed=“PerGame”,
measure_type_detailed_defense=“Base”,
)
if df is not None:
save(df, f”player_stats_{season}”)
return df

def fetch_lineup_stats(season: int = TEAM_SEASON) -> pd.DataFrame | None:
“”“5-man lineup efficiency — per-100-possession advanced metrics. Uses TEAM_SEASON.”””
print(”\n[1d] Fetching lineup stats via nba_api…”)
if not NBA_API_AVAILABLE:
print(”  ✗ nba_api not installed.”)
return None
df = nba_api_request(
LeagueDashLineups,
league_id_nullable=“10”,
season=str(season),
season_type_all_star=“Regular Season”,
per_mode_detailed=“Per100Possessions”,
measure_type_detailed_defense=“Advanced”,
group_quantity=5,
)
if df is not None:
storm_lineups = df[df[“TEAM_ID”].astype(str) == SEATTLE_STORM_TEAM_ID]
save(storm_lineups, f”storm_lineup_stats_{season}”)
save(df, f”all_lineup_stats_{season}”)
return df

def fetch_shot_chart(player_id: str, season: int = CURRENT_SEASON,
team_id: str = “0”) -> pd.DataFrame | None:
“””
Shot chart for a single player — x/y coordinates + make/miss per attempt.

```
team_id defaults to "0" (all teams) so players who were on a different team
during the stats season (e.g. Hiedeman at MIN in 2025, Dolson at WAS) get
their full shot chart rather than 0 rows from the SEA filter.

Pass team_id=SEATTLE_STORM_TEAM_ID only when you want to restrict to shots
taken as a Storm player specifically (e.g. for returners like Magbegor).

2026 Storm roster player IDs confirmed via API:
    Ezi Magbegor        : "1629496"  SEA 2025
    Dominique Malonga   : "1642798"  SEA 2025
    Natisha Hiedeman    : "1629567"  MIN 2025 → pass team_id="0"
    Jade Melbourne      : "1631141"  WAS 2025 → pass team_id="0"
    Stefanie Dolson     : "203828"   WAS 2025 → pass team_id="0"
    Lexie Brown         : "1628882"  SEA 2025
    Mackenzie Holmes    : "1642307"  SEA 2025
    Zia Cooke           : "1641660"  SEA 2025
    Jordan Horston      : "1641651"  SEA 2024 → pass team_id="0"
    Katie Lou Samuelson : "1629478"  IND 2024 → pass team_id="0"
    Rennia Davis        : "1630452"  IND 2022 → pass team_id="0"

Rookies (Fam, Johnson, Mair): no WNBA stats yet — skipped.
Find/verify IDs: stats.wnba.com → Players → click player → check URL.
"""
print(f"\n[1e] Fetching shot chart for player {player_id} via nba_api...")
if not NBA_API_AVAILABLE:
    print("  ✗ nba_api not installed.")
    return None
try:
    obj = ShotChartDetail(
        team_id=team_id,
        player_id=player_id,
        season_nullable=str(season),
        season_type_all_star="Regular Season",
        league_id="10",
        context_measure_simple="FGA",
        timeout=60,
    )
    df = obj.get_data_frames()[0]
    if df is not None and len(df) > 0:
        save(df, f"shot_chart_player_{player_id}_{season}")
    else:
        print(f"  ⚠ No shot data returned for player {player_id}")
    return df
except Exception as e:
    print(f"  ✗ Shot chart failed for player {player_id}: {e}")
    return None
```

def fetch_team_shot_chart(season: int = TEAM_SEASON) -> pd.DataFrame | None:
“”“Shot chart for the entire Storm team — all players combined. Uses TEAM_SEASON.”””
print(f”\n[1f] Fetching team shot chart via nba_api…”)
if not NBA_API_AVAILABLE:
print(”  ✗ nba_api not installed.”)
return None
try:
obj = ShotChartDetail(
team_id=SEATTLE_STORM_TEAM_ID,
player_id=0,           # 0 = all players on the team
season_nullable=str(season),
season_type_all_star=“Regular Season”,
league_id=“10”,
context_measure_simple=“FGA”,
timeout=60,
)
df = obj.get_data_frames()[0]
if df is not None and len(df) > 0:
save(df, f”team_shot_chart_{season}”)
else:
print(”  ⚠ No team shot data returned”)
return df
except Exception as e:
print(f”  ✗ Team shot chart failed: {e}”)
return None

def fetch_game_log(season: int = TEAM_SEASON) -> pd.DataFrame | None:
“”“Game-by-game log for the Storm — scores, opponents, W/L. Uses TEAM_SEASON.”””
print(”\n[1g] Fetching Storm game log via nba_api…”)
if not NBA_API_AVAILABLE:
print(”  ✗ nba_api not installed.”)
return None
try:
obj = TeamGameLogs(
team_id_nullable=SEATTLE_STORM_TEAM_ID,
season_nullable=str(season),
season_type_nullable=“Regular Season”,
league_id_nullable=“10”,
timeout=60,
)
df = obj.get_data_frames()[0]
if df is not None:
save(df, f”storm_game_log_{season}”)
return df
except Exception as e:
print(f”  ✗ Game log failed: {e}”)
return None

# ─────────────────────────────────────────────────────────────────────────────

# 2. sportsdataverse  — Play-by-Play, Box Scores & Schedule

# Pulls from pre-built Parquet files on GitHub — faster & more reliable

# than live scraping. Game IDs come from load_wnba_schedule().

# ─────────────────────────────────────────────────────────────────────────────

def fetch_sdv_schedule(season: int = CURRENT_SEASON) -> pd.DataFrame | None:
“””
Pull the full WNBA schedule for a season.
Useful for getting ESPN game IDs needed by the PBP and box score loaders.
“””
if not SDV_AVAILABLE:
print(”\n[2] Skipping sportsdataverse — not installed.”)
return None

```
print(f"\n[2a] Fetching WNBA schedule ({season}) via sportsdataverse...")
try:
    schedule = load_wnba_schedule(seasons=season)
    df = pd.DataFrame(schedule)
    storm_schedule = df[
        (df["home_display_name"] == "Seattle Storm") |
        (df["away_display_name"] == "Seattle Storm")
    ]
    save(storm_schedule, f"storm_schedule_{season}")
    save(df, f"full_schedule_{season}")
    print(f"  ✓ {len(storm_schedule)} Storm games on schedule")
    return storm_schedule
except Exception as e:
    print(f"  ✗ Schedule fetch failed: {e}")
    return None
```

def fetch_sdv_team_box_scores(season: int = CURRENT_SEASON) -> pd.DataFrame | None:
“””
Pull team-level box scores for the full season.
Data comes from ESPN via pre-built Parquet files — much faster than scraping.
“””
if not SDV_AVAILABLE:
print(”\n[2] Skipping sportsdataverse — not installed.”)
return None

```
print(f"\n[2b] Fetching team box scores ({season}) via sportsdataverse...")
try:
    team_boxes = load_wnba_team_boxscore(seasons=season)
    df = pd.DataFrame(team_boxes)
    storm_boxes = df[df["team_display_name"] == "Seattle Storm"]
    save(storm_boxes, f"storm_team_box_scores_{season}")
    save(df, f"all_team_box_scores_{season}")
    print(f"  ✓ {len(storm_boxes)} Storm team game rows found")
    return storm_boxes
except Exception as e:
    print(f"  ✗ Team box scores failed: {e}")
    return None
```

def fetch_sdv_player_box_scores(season: int = CURRENT_SEASON) -> pd.DataFrame | None:
“””
Pull player-level box scores for the full season.
Each row = one player’s stats for one game.
“””
if not SDV_AVAILABLE:
print(”\n[2] Skipping sportsdataverse — not installed.”)
return None

```
print(f"\n[2c] Fetching player box scores ({season}) via sportsdataverse...")
try:
    player_boxes = load_wnba_player_boxscore(seasons=season)
    df = pd.DataFrame(player_boxes)
    storm_players = df[df["team_display_name"] == "Seattle Storm"]
    save(storm_players, f"storm_player_box_scores_{season}")
    print(f"  ✓ {len(storm_players)} Storm player-game rows found")
    return storm_players
except Exception as e:
    print(f"  ✗ Player box scores failed: {e}")
    return None
```

def fetch_sdv_pbp(season: int = CURRENT_SEASON, game_id: str | None = None) -> pd.DataFrame | None:
“””
Pull play-by-play data.

```
Two modes:
  - Pass game_id (ESPN game ID) to pull a single game
  - Omit game_id to pull the full season PBP (large — ~millions of rows)

ESPN game IDs are in the 'game_id' column of load_wnba_schedule() output,
and also visible in ESPN URLs:
    espn.com/wnba/game/_/gameId/401578123  →  game_id = "401578123"

PBP columns of interest:
    type_text, text, period_number, clock_display_value,
    coordinate_x, coordinate_y,    # shot location
    scoring_play, score_value,      # scoring events
    athlete_id_1, athlete_id_2,     # players involved
    team_id, home_team_id
"""
if not SDV_AVAILABLE:
    print("\n[2] Skipping sportsdataverse — not installed.")
    return None

if game_id:
    print(f"\n[2d] Fetching PBP for game {game_id} via sportsdataverse...")
    try:
        pbp = load_wnba_pbp(seasons=season)
        df  = pd.DataFrame(pbp)
        game_pbp = df[df["game_id"].astype(str) == str(game_id)]
        save(game_pbp, f"pbp_game_{game_id}")
        print(f"  ✓ {len(game_pbp)} play-by-play rows for game {game_id}")
        return game_pbp
    except Exception as e:
        print(f"  ✗ PBP fetch failed: {e}")
        return None
else:
    print(f"\n[2d] Fetching full-season PBP ({season}) via sportsdataverse...")
    print("  ⚠ This is a large dataset — may take 1-2 minutes to download.")
    try:
        pbp = load_wnba_pbp(seasons=season)
        df  = pd.DataFrame(pbp)
        # Filter to Storm games only to keep file size manageable
        storm_pbp = df[
            (df["home_team_id"].astype(str) == SEATTLE_STORM_TEAM_ID) |
            (df["away_team_id"].astype(str) == SEATTLE_STORM_TEAM_ID)
        ]
        save(storm_pbp, f"storm_pbp_{season}")
        print(f"  ✓ {len(storm_pbp)} Storm play-by-play rows saved")
        return storm_pbp
    except Exception as e:
        print(f"  ✗ Full-season PBP failed: {e}")
        return None
```

# ─────────────────────────────────────────────────────────────────────────────

# 3. Basketball-Reference Scraping — Historical Stats

# ─────────────────────────────────────────────────────────────────────────────

def fetch_bref_season_stats(season: int = CURRENT_SEASON):
“””
Pull historical WNBA player season stats from Basketball-Reference.
Uses the basketball_reference_web_scraper package.
“””
if not BREF_AVAILABLE:
print(”\n[3] Skipping Basketball-Reference — package not installed.”)
return

```
print(f"\n[3] Fetching Basketball-Reference stats for {season}...")
try:
    # Player totals
    players = bref.players_season_totals(season_end_year=season, league="WNBA")
    df = pd.DataFrame(players)
    storm_players = df[df["team"] == "SEA"]
    save(storm_players, f"bref_storm_players_{season}")
    save(df, f"bref_all_players_{season}")
    print(f"  ✓ {len(storm_players)} Storm players found")
except Exception as e:
    print(f"  ✗ Basketball-Reference scrape failed: {e}")
```

# ─────────────────────────────────────────────────────────────────────────────

# 4. QUICK ANALYSIS HELPERS  — Useful transformations after data is pulled

# ─────────────────────────────────────────────────────────────────────────────

def summarize_storm_players(player_stats_df: pd.DataFrame) -> pd.DataFrame:
“””
Filter league-wide player stats down to Storm players and
compute a few key derived metrics.
“””
storm = player_stats_df[
player_stats_df[“TEAM_ID”].astype(str) == SEATTLE_STORM_TEAM_ID
].copy()

```
# True Shooting % = PTS / (2 * (FGA + 0.44 * FTA))
storm["TS_PCT"] = storm["PTS"] / (
    2 * (storm["FGA"] + 0.44 * storm["FTA"])
)

# Usage proxy (simplified)
storm["USAGE_PROXY"] = (storm["FGA"] + 0.44 * storm["FTA"] + storm["TOV"]) / storm["MIN"]

cols = [
    "PLAYER_NAME", "GP", "MIN", "PTS", "REB", "AST",
    "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT",
    "TS_PCT", "USAGE_PROXY", "PLUS_MINUS"
]
# Only keep columns that exist
cols = [c for c in cols if c in storm.columns]
return storm[cols].sort_values("PTS", ascending=False)
```

def zone_label(row) -> str:
“””
Assign a court zone label to a shot based on LOC_X / LOC_Y coordinates.
Coordinates are in tenths of feet from the basket.
“””
x, y = row[“LOC_X”], row[“LOC_Y”]
dist  = (x**2 + y**2) ** 0.5

```
if dist <= 40:                          return "Restricted Area"
elif dist <= 80 and abs(x) <= 80:      return "Paint (Non-RA)"
elif dist <= 140 and abs(x) > 80:      return "Mid-Range (Wing)"
elif dist <= 140:                       return "Mid-Range (Elbow)"
elif dist > 220:                        return "Corner 3" if abs(x) > 220 else "Above-Break 3"
else:                                   return "Above-Break 3"
```

def analyze_shot_chart(shot_df: pd.DataFrame) -> pd.DataFrame:
“””
Given a raw shot chart DataFrame, compute FG% and frequency by zone.
Returns a zone summary useful for a shot quality chart.
“””
shot_df = shot_df.copy()
shot_df[“LOC_X”] = pd.to_numeric(shot_df[“LOC_X”], errors=“coerce”)
shot_df[“LOC_Y”] = pd.to_numeric(shot_df[“LOC_Y”], errors=“coerce”)
shot_df[“SHOT_MADE_FLAG”] = pd.to_numeric(shot_df[“SHOT_MADE_FLAG”], errors=“coerce”)

```
shot_df["ZONE"] = shot_df.apply(zone_label, axis=1)

summary = (
    shot_df.groupby("ZONE")
    .agg(
        ATTEMPTS  = ("SHOT_MADE_FLAG", "count"),
        MAKES     = ("SHOT_MADE_FLAG", "sum"),
    )
    .assign(
        FG_PCT    = lambda d: (d["MAKES"] / d["ATTEMPTS"]).round(3),
        FREQUENCY = lambda d: (d["ATTEMPTS"] / d["ATTEMPTS"].sum()).round(3),
    )
    .sort_values("ATTEMPTS", ascending=False)
    .reset_index()
)
return summary
```

# ─────────────────────────────────────────────────────────────────────────────

# DIAGNOSTIC  — Run this first if the API is failing

# ─────────────────────────────────────────────────────────────────────────────

def diagnose_api(season: int = CURRENT_SEASON) -> bool:
“””
Quick connectivity test using nba_api.
Returns True if the API is reachable, False otherwise.
Run this before main() to confirm connectivity.

```
Usage:
    python -c "from storm_data_pipeline import diagnose_api; diagnose_api()"
"""
if not NBA_API_AVAILABLE:
    print("\n[DIAG] ✗ nba_api not installed. Run: pip install nba_api")
    return False

print("\n[DIAG] Testing WNBA Stats API via nba_api...")
print(f"  Endpoint : LeagueDashTeamStats  |  Season: {season}  |  LeagueID: 10")
try:
    obj = LeagueDashTeamStats(
        league_id_nullable="10",
        season=str(season),
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        measure_type_detailed_defense="Base",
        timeout=60,
    )
    df = obj.get_data_frames()[0]
    print(f"  ✓ Success — {len(df)} teams returned, {len(df.columns)} columns")
    return True
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    print("\n  Possible causes:")
    print("  • stats.wnba.com is throttling your IP — try again in 10 min")
    print("  • Your network/firewall blocks stats.wnba.com — try a VPN")
    print(f"  • Season param wrong (currently: {season})")
    print("\n  Tip: sportsdataverse functions (Section 2) hit GitHub instead")
    print("  and will work regardless of this API being down.")
    return False
```

# ─────────────────────────────────────────────────────────────────────────────

# MAIN  — Run everything

# ─────────────────────────────────────────────────────────────────────────────

def main():
print(”=” * 60)
print(” Seattle Storm Analytics — Data Collection Pipeline”)
print(f” Season: {CURRENT_SEASON}  |  {datetime.now().strftime(’%Y-%m-%d %H:%M’)}”)
print(”=” * 60)

```
# ── nba_api pulls (Section 1) ─────────────────────────────────────────────
# Team-level functions use TEAM_SEASON (2025) — 2026 roster has no shared data.
# Player-level functions use STATS_SEASON (2025) or per-player overrides.
team_stats    = fetch_team_stats()
player_stats  = fetch_player_stats()
time.sleep(3)   # be polite to the API — 3s minimum to avoid throttling

team_shot     = fetch_team_shot_chart()
time.sleep(3)

lineup_stats  = fetch_lineup_stats()
time.sleep(3)

adv_stats     = fetch_advanced_team_stats()
time.sleep(3)

game_log      = fetch_game_log()

# ── Shot chart: 2026 Storm roster — pulling 2025 stats ──────────────────
# Returners have known WNBA Stats API player IDs (from their prior seasons).
# Rookies (Fam, Johnson, Miles) are excluded — no WNBA data exists yet.
# Veteran signees (Dolson, Hiedeman, Samuelson) use their existing IDs
# from prior teams; stats will reflect their 2025 season elsewhere.
#
# To find/verify a player ID:
#   stats.wnba.com → Players → click player name → check URL for playerID=
#
# DEPARTED (do not include):
#   Nneka Ogwumike   → LA Sparks
#   Skylar Diggins   → Chicago Sky
#   Gabby Williams   → Golden State Valkyries
#   Erica Wheeler    → LA Sparks
#
# ROOKIES (no WNBA stats yet — skip shot charts):
#   Awa Fam          → 2026 Draft Pick #3
#   Flau'jae Johnson → 2026 Draft Pick #8 (via trade from Golden State)
#   Olivia Miles     → Minnesota Lynx (pick #2) — NOT on Seattle roster

# NOTE: Run the verification snippet below first to confirm all IDs,
# especially the estimated ones marked with *.
# python snippet:
#   from nba_api.stats.endpoints import LeagueDashPlayerStats
#   df = LeagueDashPlayerStats(league_id_nullable="10", season="2025",
#       season_type_all_star="Regular Season", per_mode_detailed="PerGame",
#       measure_type_detailed_defense="Base", timeout=60).get_data_frames()[0]
#   names = ["Ezi Magbegor","Dominique Malonga","Natisha Hiedeman",
#            "Jade Melbourne","Katie Lou Samuelson","Jordan Horston",
#            "Lexie Brown","Stefanie Dolson","Zia Cooke","Mackenzie Holmes",
#            "Rennia Davis","Flau'jae Johnson"]
#   print(df[df["PLAYER_NAME"].isin(names)][["PLAYER_ID","PLAYER_NAME","TEAM_ABBREVIATION"]].to_string())

STORM_PLAYER_IDS_2026 = {
    # ── Confirmed IDs from API lookup (2025 season) ──────────────────────
    "Dominique Malonga":    "1642798",  # SEA 2025
    "Ezi Magbegor":         "1629496",  # SEA 2025
    "Jade Melbourne":       "1631141",  # WAS 2025 (now SEA 2026)
    "Lexie Brown":          "1628882",  # SEA 2025
    "Mackenzie Holmes":     "1642307",  # SEA 2025
    "Natisha Hiedeman":     "1629567",  # MIN 2025 (now SEA 2026)
    "Stefanie Dolson":      "203828",   # WAS 2025 (now SEA 2026)
    "Zia Cooke":            "1641660",  # SEA 2025
    # ── Prior-season data (most recent available) ────────────────────────
    "Jordan Horston":       "1641651",  # SEA 2024 (most recent)
    "Katie Lou Samuelson":  "1629478",  # IND 2024 (most recent)
    "Rennia Davis":         "1630452",  # IND 2022 (most recent, only 13 shots — limited viz value)
    # ── No WNBA history ──────────────────────────────────────────────────
    # Flau'jae Johnson   → no WNBA history (LSU 2025, rookie in 2026)
    # ── Rookies (no WNBA history) ────────────────────────────────────────
    # Awa Fam             → 2026 draft pick #3
    # Taina Mair          → 2026 draft pick
    # ── Departed — do not include ────────────────────────────────────────
    # Jewell Loyd         → not on 2026 roster
    # Brittney Sykes      → departed
    # Gabby Williams      → Golden State Valkyries
    # Nneka Ogwumike      → LA Sparks
    # Skylar Diggins      → Chicago Sky
}

# Per-player season overrides — use most recent available data
PLAYER_SEASON_OVERRIDES = {
    "Jordan Horston":       2024,
    "Katie Lou Samuelson":  2024,
    "Rennia Davis":         2022,
}

# Players whose stats season was spent at SEA — filter to Storm shots only.
# Everyone else defaults to team_id="0" (all teams) so we get their full
# shot chart regardless of which franchise they were on that season.
SEA_IN_STATS_SEASON = {
    "Ezi Magbegor", "Dominique Malonga", "Lexie Brown",
    "Mackenzie Holmes", "Zia Cooke",
}

for name, pid in STORM_PLAYER_IDS_2026.items():
    season  = PLAYER_SEASON_OVERRIDES.get(name, STATS_SEASON)
    team_id = SEATTLE_STORM_TEAM_ID if name in SEA_IN_STATS_SEASON else "0"
    print(f"\n  → Shot chart ({season} stats, team_id={team_id}): {name}")
    fetch_shot_chart(pid, season=season, team_id=team_id)
    time.sleep(3)

# ── sportsdataverse pulls ─────────────────────────────────────────────────
schedule     = fetch_sdv_schedule()
team_boxes   = fetch_sdv_team_box_scores()
player_boxes = fetch_sdv_player_box_scores()

# Full-season PBP (large download — comment out if you only need box scores)
# storm_pbp = fetch_sdv_pbp()

# Single-game PBP — grab a game_id from the schedule output above
# fetch_sdv_pbp(game_id="401578123")

# ── Basketball-Reference ──────────────────────────────────────────────────
fetch_bref_season_stats()

# ── Quick derived analysis ────────────────────────────────────────────────
if player_stats is not None:
    print("\n[4] Computing Storm player summary...")
    summary = summarize_storm_players(player_stats)
    save(summary, f"storm_player_summary_{CURRENT_SEASON}")
    print("\nStorm Player Summary (top 8 by PPG):")
    print(summary.head(8).to_string(index=False))

if team_shot is not None:
    print("\n[4] Analyzing Storm shot chart by zone...")
    zones = analyze_shot_chart(team_shot)
    save(zones, f"storm_shot_zones_{CURRENT_SEASON}")
    print("\nShot Zone Summary:")
    print(zones.to_string(index=False))

print("\n" + "=" * 60)
print(f" Done! All files saved to ./{OUTPUT_DIR}/")
print("=" * 60)
```

if **name** == “**main**”:
    main()