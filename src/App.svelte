<script>
  import { untrack } from 'svelte';
  import initialData from './data.json';
  import thirdPlaceData from './3rd_place_data.json';
  import officialData from './data_official.json';
  import i18n from './i18n.json';
  import './styles/app.css'; // Ensure this is imported before any component-specific styles if they override global ones
  import FilterSelect from './components/FilterSelect.svelte';
  import MatchCard from './components/MatchCard.svelte';
  import StandingsTable from './components/StandingsTable.svelte';
  import Bracket from './components/Bracket.svelte';
  import TeamStatsTable from './components/TeamStatsTable.svelte';

  // --- STATE (RUNES) ---
  const STORAGE_KEY = 'retro_cup_26';

  // Helper to get a fresh set of all match templates
  function getAllInitialMatchesTemplates() {
    return [
      ...structuredClone(initialData.matches.group_stage),
      ...structuredClone(initialData.matches.r32),
      ...structuredClone(initialData.matches.r16),
      ...structuredClone(initialData.matches.qf),
      ...structuredClone(initialData.matches.sf),
      ...structuredClone(initialData.matches.third),
      ...structuredClone(initialData.matches.final)
    ].sort((a, b) => a.id - b.id); // Ensure consistent order
  }

  function loadMatches(mode) {
    const baseMatches = getAllInitialMatchesTemplates();
    const matchesMap = new Map(baseMatches.map(m => [m.id, m]));

    try {
      let parsed = null;
      if (mode === 'simulation') {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved)
          parsed = JSON.parse(saved);
      } else {
        parsed = officialData;
      }
      if (Array.isArray(parsed)) {
        parsed.forEach(savedMatch => {
          const baseMatch = matchesMap.get(savedMatch.id);
          if (baseMatch) {
            baseMatch.played = !!savedMatch.played;
            ['team1', 'team2'].forEach(tKey => {
              if (savedMatch[tKey]) {
                ['score', 'yellow_cards', 'red_cards', 'penalties'].forEach(sKey => {
                  baseMatch[tKey][sKey] = savedMatch[tKey][sKey] ?? 0;
                });
              }
            });
          }
        });
      }
    } catch (e) {
      console.error("Error loading matches from localStorage:", e);
    }
    return baseMatches;
  }

  let appMode = $state('simulation'); // simulation, official
  let matches = $state(loadMatches('simulation'));
  let currentTab = $state('matches'); // matches, bracket, standings, etc
  let selectedVenue = $state(null); // null for 'all venues'
  let selectedDate = $state(null); // null for 'all dates'
  let selectedGroup = $state(null); // null for 'all groups'
  let selectedTeam = $state(null); // null for 'all teams'
  let locale = $state(localStorage.getItem(STORAGE_KEY + '_locale') || 'en'); // Persisted 'en' or 'pt'

  // --- UTILS ---
  const t = $derived(i18n[locale]);
  const tabLabels = $derived(t.tabs);
  const teamCodes = Object.keys(initialData.teams); // Consistent order for sprite lookup
  const langTag = $derived(locale === 'en' ? 'en-US' : 'pt-BR');

  const getLocalDateStr = (dateStr) => {
    if (!dateStr || dateStr === 'TBD') return 'TBD';
    const d = new Date(dateStr);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'TBD';
    return new Date(dateStr).toLocaleString(langTag, {
      weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
    }).toUpperCase();
  };

  const formatShortDate = (dateStr) => {
    if (dateStr === null) return t.ui.all_dates;
    const [y, m, d] = dateStr.split('-').map(Number);
    const date = new Date(y, m - 1, d); // Parse as local time to avoid TZ shifts
    return date.toLocaleDateString(langTag, {
      weekday: 'short', month: 'short', day: 'numeric'
    }).toUpperCase();
  };

  const compareTeams = (a, b) => {
    return (
      b.pts - a.pts ||
      b.gd - a.gd ||
      b.gf - a.gf ||
      ((b.yc * -1) + (b.rc * -3)) - ((a.yc * -1) + (a.rc * -3)) ||
      // Safe access in case a team rank is missing during an update
      ((initialData.teams[a.code]?.rank || 999) - (initialData.teams[b.code]?.rank || 999))
    );
  };

  const getWinner = (match) => {
    if (!match || !match.played) return null;
    if (match.team1.score > match.team2.score) return match.team1.code;
    if (match.team2.score > match.team1.score) return match.team2.code;

    // Penalty fallback - check if a winner exists in penalties
    const p1 = match.team1.penalties || 0;
    const p2 = match.team2.penalties || 0;
    if (p1 > p2) return match.team1.code;
    if (p2 > p1) return match.team2.code;

    return null;
  };

  const resolveSlot = (slotCode, stageMatches = [], qualifiersRef) => {
    if (!slotCode) return 'TBD';
    if (slotCode.startsWith('W') || slotCode.startsWith('L')) {
      const type = slotCode[0];
      const matchId = parseInt(slotCode.slice(1));
      
      const match = stageMatches.find(m => m.id === matchId);
      
      if (type === 'W') return getWinner(match) || 'TBD';
      if (type === 'L') {
        if (!match || !match.played) return 'TBD';
        const winner = getWinner(match);
        if (!winner) return 'TBD';
        return winner === match.team1.code ? match.team2.code : match.team1.code;
      }
    }
    return qualifiersRef[slotCode] || 'TBD';
  };

  // --- AUTOSAVE ---
  $effect(() => {
    // Trigger this effect when 'matches' actually changes.
    // Untrack 'appMode' to prevent the effect from firing immediately during a mode switch.
    const currentMatches = matches;
    if (untrack(() => appMode) !== 'simulation')
      return;

    // Save only the user-modified data (scores, cards, penalties, played status)
    const dataToSave = currentMatches.map(match => ({
      id: match.id,
      played: match.played,
      team1: {
        score: match.team1.score, yellow_cards: match.team1.yellow_cards, red_cards: match.team1.red_cards, penalties: match.team1.penalties
      },
      team2: {
        score: match.team2.score, yellow_cards: match.team2.yellow_cards, red_cards: match.team2.red_cards, penalties: match.team2.penalties
      }
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));
  });

  $effect(() => {
    localStorage.setItem(STORAGE_KEY + '_locale', locale);
  });

  // Re-load matches when switching modes
  $effect(() => {
    matches = loadMatches(appMode);
  });

  // Reset date filter when changing tabs to prevent empty views
  $effect(() => {
    currentTab;
    selectedDate = null;
    selectedVenue = null;
    selectedGroup = null;
    selectedTeam = null;
  });

  // --- LOGIC ---
  function resetData() {
    if (confirm(t.ui.reset_confirm)) {
      matches = getAllInitialMatchesTemplates();
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  /**
   * Unified mutator for all match data. 
   * Handles both group stage and dynamic knockout matches.
   */
   function updateMatchData(matchId, teamKey, statKey, delta) {
    if (appMode === 'official')
      return;
    const match = matches.find(m => m.id === matchId); // All matches are already in the array

    if (match) {
      const currentVal = Number(match[teamKey][statKey] || 0);
      match[teamKey][statKey] = Math.max(0, currentVal + delta);
      if (statKey === 'score' || statKey === 'penalties') match.played = true;
    }
  }

  function resetMatchData(matchId) {
    if (appMode === 'official')
      return;
    const match = matches.find(m => m.id === matchId);
    if (match) {
      match.played = false;
      ['team1', 'team2'].forEach(tKey => {
        if (match[tKey]) {
          match[tKey].score = 0;
          match[tKey].yellow_cards = 0;
          match[tKey].red_cards = 0;
          match[tKey].penalties = 0;
        }
      });
    }
  }

  // --- COMPUTED STANDINGS ---
  let liveStandings = $derived.by(() => {
    const stats = {};
    Object.keys(initialData.teams).forEach(code => {
      const teamInfo = initialData.teams[code];
      stats[code] = {
        code,
        name: t.teams[code],
        mp: 0, pts: 0, gf: 0, ga: 0, gd: 0, yc: 0, rc: 0, w: 0, d: 0, l: 0
      };
    });

    matches.forEach(m => {
      // Only process group stage matches for the standings table
      if (m.id > 72) return;
      
      // A game is counted if manually marked played
      if (!m.played) return;
      
      const t1 = stats[m.team1.code];
      const t2 = stats[m.team2.code];

      // Safety check: skip if the team code is "TBD" or missing from the initial teams list
      if (!t1 || !t2) return;

      t1.mp++; t2.mp++;
      t1.gf += m.team1.score; t1.ga += m.team2.score;
      t2.gf += m.team2.score; t2.ga += m.team1.score;
      t1.yc += (m.team1.yellow_cards || 0); t1.rc += (m.team1.red_cards || 0);
      t2.yc += (m.team2.yellow_cards || 0); t2.rc += (m.team2.red_cards || 0);

      if (m.team1.score > m.team2.score) {
        t1.pts += 3; t1.w++; t2.l++;
      } else if (m.team2.score > m.team1.score) {
        t2.pts += 3; t2.w++; t1.l++;
      } else {
        t1.pts += 1; t2.pts += 1;
        t1.d++; t2.d++;
      }

      t1.gd = t1.gf - t1.ga;
      t2.gd = t2.gf - t2.ga;
    });
    return stats;
  });

  // Get the pool of matches for the currently active tab
  let activeMatchesPool = $derived.by(() => {
    if (currentTab === 'matches') return matches.filter(m => m.id <= 72); // Group stage matches
    if (currentTab === 'r32') return r32Matches;
    if (currentTab === 'r16') return r16Matches;
    if (currentTab === 'qf') return qfMatches;
    if (currentTab === 'sf') return sfMatches;
    if (currentTab === 'third') return thirdMatch;
    if (currentTab === 'final') return finalMatch;
    return [];
  });

  // Extract unique venues from the current pool
  let activeVenues = $derived.by(() => {
    const venues = [...new Set(activeMatchesPool // Use activeMatchesPool for relevant filters
      .map(m => m.venue))]
      .filter(v => v && v !== 'TBD')
      .sort();
    return [null, ...venues];
  });

  // Extract unique dates from the current pool
  let activeDates = $derived.by(() => {
    const dates = [...new Set(activeMatchesPool // Use activeMatchesPool for relevant filters
      .map(m => getLocalDateStr(m.date)))]
      .filter(d => d && d !== 'TBD')
      .sort();
    return [null, ...dates];
  });

  // Extract unique groups for filtering
  let groupOptions = $derived.by(() => {
    const groups = Object.keys(initialData.groups).sort();
    return [
      { id: null, label: t.ui.all_groups },
      ...groups.map(g => ({ id: g, label: `${t.standings.group} ${g}` }))
    ];
  });

  // Extract all teams for filtering
  let teamOptions = $derived.by(() => {
    const teams = Object.keys(initialData.teams).map(code => ({
      id: code,
      label: t.teams[code] || code
    })).sort((a, b) => a.label.localeCompare(b.label));
    return [
      { id: null, label: t.ui.all_teams },
      ...teams
    ];
  });
  // Count matches per date in the current pool
  let activeMatchCounts = $derived.by(() => {
    const counts = { [null]: activeMatchesPool.length };
    activeMatchesPool.forEach(m => {
      const d = getLocalDateStr(m.date);
      if (d && d !== 'TBD') counts[d] = (counts[d] || 0) + 1;
    });
    return counts;
  });

  // Final filtered list for the UI
  let filteredMatches = $derived.by(() => {
    return activeMatchesPool.filter(m => 
      (!selectedDate || getLocalDateStr(m.date) === selectedDate) && 
      (!selectedVenue || m.venue === selectedVenue) &&
      (!selectedGroup || initialData.teams[m.team1.code]?.group === selectedGroup) &&
      (!selectedTeam || m.team1.code === selectedTeam || m.team2.code === selectedTeam)
    );
  });

  function resolveGroupStandings(teamCodes, liveStandings, groupMatches) {
    const teams = teamCodes.map(code => liveStandings[code]);
    
    // Helper to recursively sort a subset of teams that are tied on points
    function sortSubset(subset) {
      if (subset.length <= 1) return subset;
      
      // H2H mini-table logic (works for any subset size >= 2, including 2, 3, or 4 teams)
      const codes = subset.map(t => t.code);
      const miniStats = {};
      codes.forEach(code => {
        miniStats[code] = { pts: 0, gd: 0, gf: 0 };
      });
      
      groupMatches.forEach(m => {
        if (codes.includes(m.team1.code) && codes.includes(m.team2.code)) {
          const c1 = m.team1.code;
          const c2 = m.team2.code;
          const s1 = m.team1.score;
          const s2 = m.team2.score;
          
          miniStats[c1].gf += s1;
          miniStats[c2].gf += s2;
          miniStats[c1].gd += (s1 - s2);
          miniStats[c2].gd += (s2 - s1);
          
          if (s1 > s2) miniStats[c1].pts += 3;
          else if (s2 > s1) miniStats[c2].pts += 3;
          else {
            miniStats[c1].pts += 1;
            miniStats[c2].pts += 1;
          }
        }
      });
      
      const sortedSubset = [...subset].sort((a, b) => {
        const statsA = miniStats[a.code];
        const statsB = miniStats[b.code];
        return (
          statsB.pts - statsA.pts ||
          statsB.gd - statsA.gd ||
          statsB.gf - statsA.gf
        );
      });
      
      // Group remaining ties to resolve recursively
      const groups = [];
      let currentGroup = [sortedSubset[0]];
      for (let i = 1; i < sortedSubset.length; i++) {
        const prev = sortedSubset[i - 1];
        const curr = sortedSubset[i];
        const sPrev = miniStats[prev.code];
        const sCurr = miniStats[curr.code];
        if (sPrev.pts === sCurr.pts && sPrev.gd === sCurr.gd && sPrev.gf === sCurr.gf) {
          currentGroup.push(curr);
        } else {
          groups.push(currentGroup);
          currentGroup = [curr];
        }
      }
      groups.push(currentGroup);
      
      if (groups.length === 1) {
        return [...subset].sort(compareTeams);
      }
      
      let resolved = [];
      groups.forEach(g => {
        resolved = resolved.concat(sortSubset(g));
      });
      return resolved;
    }
    
    // Group by overall points first
    const pointsGroups = {};
    teams.forEach(t => {
      pointsGroups[t.pts] = pointsGroups[t.pts] || [];
      pointsGroups[t.pts].push(t);
    });
    
    const sortedPoints = Object.keys(pointsGroups).map(Number).sort((a, b) => b - a);
    let finalStandings = [];
    sortedPoints.forEach(pts => {
      finalStandings = finalStandings.concat(sortSubset(pointsGroups[pts]));
    });
    return finalStandings;
  }

  let groupsWithStandings = $derived.by(() => {
    const result = {};
    Object.keys(initialData.groups).forEach(name => {
      const teamCodes = initialData.groups[name];
      const groupMatches = matches.filter(m => 
        m.id <= 72 && 
        m.played &&
        teamCodes.includes(m.team1.code) && 
        teamCodes.includes(m.team2.code)
      );
      result[name] = resolveGroupStandings(teamCodes, liveStandings, groupMatches);
    });
    return result;
  });

  // Derive sorted list of all 3rd place teams to avoid duplicate sorting
  let sortedThirdPlaceTeams = $derived.by(() => {
    const thirds = [];
    Object.keys(groupsWithStandings).forEach(name => {
      const g = groupsWithStandings[name];
      if (g[2]) {
        // We need to keep track of the origin group for the allocation lookup
        thirds.push({ ...g[2], originGroup: name });
      }
    });
    return thirds.sort(compareTeams);
  });

  // --- KNOCKOUT DERIVATION ---
  let qualifiersData = $derived.by(() => {
    const top2 = {};
    Object.keys(groupsWithStandings).forEach(name => {
      const g = groupsWithStandings[name];
      top2[`1${name}`] = g[0]?.code || 'TBD';
      top2[`2${name}`] = g[1]?.code || 'TBD';
    });

    // Pick best 8 third-place teams from the derived sorted list
    const sortedThirds = sortedThirdPlaceTeams.slice(0, 8);
    
    // Determine the combination of groups (sorted alphabetically for lookup key)
    const comboKey = sortedThirds.map(t => t.originGroup).sort().join('');

    // Allocation table defined by FIFA for the 48-team / 12-group format
    const allocation = thirdPlaceData[comboKey];

    // Debug log for R32 third-place allocation
    if (sortedThirds.length === 8) {
      console.log(`[R32 Debug] Combo Key: ${comboKey} | Result:`, allocation || 'NOT FOUND');
    }

    // Mapping the 8 allocation indices to the specific FIFA slot names and their opponents
    const slotMapping = [
      { slot: '3CEFHI', vs: '1A' },
      { slot: '3EFGIJ', vs: '1B' },
      { slot: '3BEFIJ', vs: '1D' },
      { slot: '3ABCDF', vs: '1E' },
      { slot: '3AEHIJ', vs: '1G' },
      { slot: '3CDFGH', vs: '1I' },
      { slot: '3DEIJL', vs: '1K' },
      { slot: '3EHIJK', vs: '1L' }
    ];

    const hasError = sortedThirds.length === 8 && !allocation;

    if (allocation && !hasError) {
      // Map each of the 8 matches to the 3rd place team from the assigned group
      allocation.forEach((val, i) => {
        // Strip the "3" prefix from values like "3E" to get just the group letter
        const groupName = val.startsWith('3') ? val.slice(1) : val;
        const team = sortedThirds.find(t => t.originGroup === groupName);
        top2[slotMapping[i].slot] = team?.code || 'TBD';
      });
    } else {
      // Fallback to filling slots in order if the specific combination is missing
      slotMapping.forEach((m, i) => {
        top2[m.slot] = sortedThirds[i]?.code || 'TBD';
      });
    }

    return { slots: top2, hasError };
  });

  /**
   * Reorders knockout matches for the Bracket view.
   * This ensures that matches that feed into each other are positioned correctly
   * in the visualization (e.g., Match 89 sits next to 74 and 77).
   */
  let knockoutRounds = $derived([
    { 
      label: tabLabels.r32, 
      matches: [74, 77, 73, 75, 83, 84, 81, 82, 76, 78, 79, 80, 86, 88, 85, 87]
        .map(id => r32Matches.find(m => m.id === id)) 
    },
    { 
      label: tabLabels.r16, 
      matches: [89, 90, 93, 94, 91, 92, 95, 96]
        .map(id => r16Matches.find(m => m.id === id)) 
    },
    { 
      label: tabLabels.qf, 
      matches: [97, 98, 99, 100]
        .map(id => qfMatches.find(m => m.id === id)) 
    },
    { 
      label: tabLabels.sf, 
      matches: [101, 102].map(id => sfMatches.find(m => m.id === id)) 
    },
    { 
      label: `${tabLabels.final} & ${tabLabels.third}`, 
      matches: [...finalMatch, ...thirdMatch] 
    }
  ]);

  let qualifiers = $derived(qualifiersData.slots);
  let isAllocationError = $derived(qualifiersData.hasError);

  // Map to store the rank (1-8) of the qualifying third-place teams
  let bestThirdsRankMap = $derived.by(() => {
    const map = {};
    sortedThirdPlaceTeams.slice(0, 8).forEach((t, i) => map[t.code] = i + 1);
    return map;
  });

  let r32Matches = $derived.by(() => {
    return initialData.matches.r32.map(layout => {
      // Try to find if user has manually entered/saved a knockout score already
      const savedMatch = matches.find(m => m.id === layout.id);
      return {
        ...layout,
        team1: {
          code: resolveSlot(layout.homeSlot, [], qualifiers),
          score: savedMatch?.team1.score || 0,
          penalties: savedMatch?.team1.penalties || 0,
          yellow_cards: savedMatch?.team1.yellow_cards || 0,
          red_cards: savedMatch?.team1.red_cards || 0
        },
        team2: {
          code: resolveSlot(layout.awaySlot, [], qualifiers),
          score: savedMatch?.team2.score || 0,
          penalties: savedMatch?.team2.penalties || 0,
          yellow_cards: savedMatch?.team2.yellow_cards || 0,
          red_cards: savedMatch?.team2.red_cards || 0
        },
        played: savedMatch?.played || false
      };
    });
  });

  let r16Matches = $derived.by(() => {
    return initialData.matches.r16.map(layout => {
      const savedMatch = matches.find(m => m.id === layout.id);
      return {
        ...layout,
        team1: {
          ...savedMatch?.team1,
          code: resolveSlot(layout.homeSlot, r32Matches, qualifiers),
          score: savedMatch?.team1.score || 0,
          penalties: savedMatch?.team1.penalties || 0,
          yellow_cards: savedMatch?.team1.yellow_cards || 0,
          red_cards: savedMatch?.team1.red_cards || 0
        },
        team2: {
          ...savedMatch?.team2,
          code: resolveSlot(layout.awaySlot, r32Matches, qualifiers),
          score: savedMatch?.team2.score || 0,
          penalties: savedMatch?.team2.penalties || 0,
          yellow_cards: savedMatch?.team2.yellow_cards || 0,
          red_cards: savedMatch?.team2.red_cards || 0
        },
        played: savedMatch?.played || false
      };
    });
  });

  let qfMatches = $derived.by(() => {
    return initialData.matches.qf.map(layout => {
      const savedMatch = matches.find(m => m.id === layout.id);
      return {
        ...layout,
        team1: { ...savedMatch?.team1, code: resolveSlot(layout.homeSlot, r16Matches, qualifiers), score: savedMatch?.team1.score || 0 },
        team2: { ...savedMatch?.team2, code: resolveSlot(layout.awaySlot, r16Matches, qualifiers), score: savedMatch?.team2.score || 0 },
        played: savedMatch?.played || false
      };
    });
  });

  let sfMatches = $derived.by(() => {
    return initialData.matches.sf.map(layout => {
      const savedMatch = matches.find(m => m.id === layout.id);
      return {
        ...layout,
        team1: { ...savedMatch?.team1, code: resolveSlot(layout.homeSlot, qfMatches, qualifiers), score: savedMatch?.team1.score || 0 },
        team2: { ...savedMatch?.team2, code: resolveSlot(layout.awaySlot, qfMatches, qualifiers), score: savedMatch?.team2.score || 0 },
        played: savedMatch?.played || false
      };
    });
  });

  let thirdMatch = $derived.by(() => {
    return initialData.matches.third.map(layout => {
      const savedMatch = matches.find(m => m.id === layout.id);
      return {
        ...layout,
        team1: { ...savedMatch?.team1, code: resolveSlot(layout.homeSlot, sfMatches, qualifiers), score: savedMatch?.team1.score || 0 },
        team2: { ...savedMatch?.team2, code: resolveSlot(layout.awaySlot, sfMatches, qualifiers), score: savedMatch?.team2.score || 0 },
        played: savedMatch?.played || false
      };
    });
  });

  let finalMatch = $derived.by(() => {
    return initialData.matches.final.map(layout => {
      const savedMatch = matches.find(m => m.id === layout.id);
      return {
        ...layout,
        team1: { ...savedMatch?.team1, code: resolveSlot(layout.homeSlot, sfMatches, qualifiers), score: savedMatch?.team1.score || 0 },
        team2: { ...savedMatch?.team2, code: resolveSlot(layout.awaySlot, sfMatches, qualifiers), score: savedMatch?.team2.score || 0 },
        played: savedMatch?.played || false
      };
    });
  });

  let allTournamentStats = $derived.by(() => {
    const stats = {};
    Object.keys(initialData.teams).forEach(code => {
      stats[code] = {
        code,
        name: t.teams[code] || code,
        mp: 0, pts: 0, gf: 0, ga: 0, gd: 0, yc: 0, rc: 0, w: 0, d: 0, l: 0
      };
    });

    const allMatches = [
      ...matches.filter(m => m.id <= 72),
      ...r32Matches,
      ...r16Matches,
      ...qfMatches,
      ...sfMatches,
      ...thirdMatch,
      ...finalMatch
    ];

    allMatches.forEach(m => {
      if (!m || !m.played) return;
      const t1 = stats[m.team1.code];
      const t2 = stats[m.team2.code];
      if (!t1 || !t2) return;

      t1.mp++; t2.mp++;
      t1.gf += (m.team1.score || 0); t1.ga += (m.team2.score || 0);
      t2.gf += (m.team2.score || 0); t2.ga += (m.team1.score || 0);
      t1.yc += (m.team1.yellow_cards || 0); t1.rc += (m.team1.red_cards || 0);
      t2.yc += (m.team2.yellow_cards || 0); t2.rc += (m.team2.red_cards || 0);

      const s1 = m.team1.score || 0;
      const s2 = m.team2.score || 0;

      if (s1 > s2) {
        t1.pts += 3; t1.w++; t2.l++;
      } else if (s2 > s1) {
        t2.pts += 3; t2.w++; t1.l++;
      } else {
        t1.pts += 1; t2.pts += 1;
        t1.d++; t2.d++;
      }

      t1.gd = t1.gf - t1.ga;
      t2.gd = t2.gf - t2.ga;
    });

    return Object.values(stats);
  });

</script>

{#snippet globalFiltersUI()}
  <div class="arcade-filters">
    <FilterSelect 
      label={t.ui.filter_by} 
      options={activeDates.map(d => ({ id: d, label: formatShortDate(d) + (d !== null ? ` [${activeMatchCounts[d]}]` : '') }))} 
      bind:value={selectedDate} 
      placeholder={t.ui.all_dates} 
    />
    <FilterSelect 
      label={t.ui.select_venue} 
      options={activeVenues.map(v => ({ id: v, label: v ? (initialData.venues[v] || v) : t.ui.all_venues }))} 
      bind:value={selectedVenue} 
      placeholder={t.ui.all_venues} 
    />
    {#if currentTab === 'matches'}
      <FilterSelect 
        label={t.ui.filter_group} 
        options={groupOptions} 
        bind:value={selectedGroup} 
        placeholder={t.ui.all_groups} 
      />
      <FilterSelect 
        label={t.ui.filter_team} 
        options={teamOptions} 
        bind:value={selectedTeam} 
        placeholder={t.ui.all_teams} 
      />
    {/if}
  </div>
{/snippet}

<div class="app-container">
  <header class="arcade-header">
    <h1>RETRO CUP 26</h1>
    <p class="subtitle">{t.ui.tracker} v1.0 // {t.ui.ready}</p>
    <div class="lang-switcher">
      <button class:active-lang={locale === 'en'} onclick={() => locale = 'en'}>EN</button>
      <button class:active-lang={locale === 'pt'} onclick={() => locale = 'pt'}>PT</button>
    </div>
    <div class="lang-switcher mode-switcher">
      <button class:active-lang={appMode === 'simulation'} onclick={() => appMode = 'simulation'}>{t.ui.mode_simulation}</button>
      <button class:active-lang={appMode === 'official'} onclick={() => appMode = 'official'}>{t.ui.mode_official}</button>
    </div>
  </header>

  <nav class="arcade-nav">
    <div class="nav-row">
      <button class:active-btn={currentTab === 'matches'} onclick={() => currentTab = 'matches'}>
        [ {tabLabels.matches} ]
      </button>
      <button class:active-btn={currentTab === 'standings'} onclick={() => currentTab = 'standings'}>
        [ {tabLabels.standings} ]
      </button>
      <button class:active-btn={currentTab === 'stats'} onclick={() => currentTab = 'stats'}>
        [ {tabLabels.stats} ]
      </button>
      <button class:active-btn={currentTab === 'bracket'} onclick={() => currentTab = 'bracket'}>
        [ {tabLabels.bracket} ]
      </button>
    </div>
    <div class="nav-row">
      <button class:active-btn={currentTab === 'r32'} onclick={() => currentTab = 'r32'}>[ {tabLabels.r32} ]</button>
      <button class:active-btn={currentTab === 'r16'} onclick={() => currentTab = 'r16'}>[ {tabLabels.r16} ]</button>
      <button class:active-btn={currentTab === 'qf'} onclick={() => currentTab = 'qf'}>[ {tabLabels.qf} ]</button>
    </div>
    <div class="nav-row">
      <button class:active-btn={currentTab === 'sf'} onclick={() => currentTab = 'sf'}>[ {tabLabels.sf} ]</button>
      <button class:active-btn={currentTab === 'third'} onclick={() => currentTab = 'third'}>[ {tabLabels.third} ]</button>
      <button class:active-btn={currentTab === 'final'} onclick={() => currentTab = 'final'}>[ {tabLabels.final} ]</button>
    </div>
    <div class="nav-row">
      {#if appMode === 'simulation'}
        <button class="reset-btn-nav" onclick={resetData}>
          [ {t.ui.reset} ]
        </button>
      {/if}
    </div>
  </nav>

  <main class="content-area">
    {#if isAllocationError && currentTab === 'r32'}
      <div class="arcade-error-banner" role="alert">
        <div>*** {t.ui.machine_error} ***</div>
        <div style="font-size: 8px; margin-top: 8px;">{t.ui.system_malfunction}</div>
        <div style="font-size: 8px; margin-top: 4px;">{t.ui.contact_operator}</div>
      </div>
    {/if}

    {#if ['matches', 'r32', 'r16', 'qf', 'sf', 'third', 'final'].includes(currentTab)}
      <div class="matches-container">
        <h2 class="section-title">[ {tabLabels[currentTab]} ]</h2>
        {@render globalFiltersUI()}

        {#each filteredMatches as match (match.id)}
          <MatchCard 
            {match} 
            {t} 
            {teamCodes} 
            venues={initialData.venues} 
            onUpdate={updateMatchData} 
            onReset={resetMatchData} 
            isReadOnly={appMode === 'official'}
            {formatDate} 
          />
        {/each}
      </div>
    {:else if currentTab === 'bracket'}
      <div class="matches-container">
        <h2 class="section-title">[ {tabLabels.bracket} ]</h2>
        <Bracket 
          rounds={knockoutRounds} 
          {t} 
          {teamCodes} 
        />
      </div>
    {:else if currentTab === 'stats'}
      <TeamStatsTable
        stats={allTournamentStats}
        {t}
        {teamCodes}
      />
    {:else}
      <div class="standings-container">
        {#each Object.entries(groupsWithStandings) as [groupName, teams]}
          <StandingsTable 
            {groupName} 
            {teams} 
            {t} 
            {teamCodes} 
            {qualifiers} 
            {bestThirdsRankMap} 
          />
        {/each}
      </div>
    {/if}
  </main>

  <footer class="arcade-footer">
    <p>{t.footer.line1}</p>
    <p>{t.footer.line2}</p>
    <p>{t.footer.line3}</p>
    <p class="footer-credits">
      <a href="https://flagpedia.net" target="_blank" rel="noopener noreferrer">{t.footer.credits}</a>
    </p>
  </footer>
</div>