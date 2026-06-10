<script>
  import initialData from './data.json';
  import thirdPlaceData from './3rd_place_data.json';
  import i18n from './i18n.json';
  import './styles/app.css';

  // --- STATE (RUNES) ---
  const STORAGE_KEY = 'retro_cup_26';

  function initMatches() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) return structuredClone(initialData.matches.group_stage);
      const parsed = JSON.parse(saved);
      return Array.isArray(parsed) ? parsed : structuredClone(initialData.matches.group_stage);
    } catch (e) {
      return structuredClone(initialData.matches.group_stage);
    }
  }

  let matches = $state(initMatches());
  let currentTab = $state('matches'); // matches, r32, r16, qf, sf, third, final, standings
  let selectedVenue = $state(null);
  let selectedDate = $state('all');
  let isDateFilterOpen = $state(false);
  let isVenueFilterOpen = $state(false);
  let venueFilterContainer = $state();
  let locale = $state('en'); // 'en' or 'pt'
  let dateFilterContainer = $state();

  // --- UTILS ---
  const t = $derived(i18n[locale]);
  const tabLabels = $derived(t.tabs);
  const teamCodes = Object.keys(initialData.teams); // Consistent order for sprite lookup
  const langTag = $derived(locale === 'en' ? 'en-US' : 'pt-BR');

  const formatDate = (dateStr) => {
    if (!dateStr) return 'TBD';
    return new Date(dateStr).toLocaleString(langTag, {
      weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
    }).toUpperCase();
  };

  const formatShortDate = (dateStr) => {
    if (dateStr === 'all') return t.ui.all_dates;
    return new Date(dateStr + 'T12:00:00Z').toLocaleDateString(langTag, {
      weekday: 'short', month: 'short', day: 'numeric'
    }).toUpperCase();
  };

  const compareTeams = (a, b) => {
    return (
      b.pts - a.pts ||
      b.gd - a.gd ||
      b.gf - a.gf ||
      (b.w || 0) - (a.w || 0) || // FIFA Tie-breaker: Number of wins
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
    localStorage.setItem(STORAGE_KEY, JSON.stringify(matches));
  });

  // Reset date filter when changing tabs to prevent empty views
  $effect(() => {
    currentTab;
    selectedDate = 'all';
    isDateFilterOpen = false;
    selectedVenue = null;
    isVenueFilterOpen = false;
  });

  // --- LOGIC ---
  function resetData() {
    if (confirm(t.ui.reset_confirm)) {
      matches = structuredClone(initialData.matches.group_stage);
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  /**
   * Unified mutator for all match data. 
   * Handles both group stage and dynamic knockout matches.
   */
   function updateMatchData(matchId, teamKey, statKey, delta) {
    let match = matches.find(m => m.id === matchId);
    
    if (!match && matchId > 72) {
      // Initialize knockout match from template if it doesn't exist in state yet
      const categories = ['r32', 'r16', 'qf', 'sf', 'third', 'final'];
      let template;
      for (const cat of categories) {
        template = initialData.matches[cat].find(m => m.id === matchId);
        if (template) break;
      }
      
      if (template) {
        match = structuredClone(template);
        matches.push(match);
      }
    }

    if (match) {
      const currentVal = Number(match[teamKey][statKey] || 0);
      match[teamKey][statKey] = Math.max(0, currentVal + delta);
      if (statKey === 'score' || statKey === 'penalties') match.played = true;
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
    if (currentTab === 'matches') return matches.filter(m => m.id <= 72);
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
    const venues = [...new Set(activeMatchesPool
      .map(m => m.venue))]
      .filter(v => v && v !== 'TBD')
      .sort();
    return [null, ...venues];
  });

  // Extract unique dates from the current pool
  let activeDates = $derived.by(() => {
    const dates = [...new Set(activeMatchesPool
      .map(m => m.date?.split('T')[0]))]
      .filter(d => d && d !== 'TBD')
      .sort();
    return ['all', ...dates];
  });

  // Count matches per date in the current pool
  let activeMatchCounts = $derived.by(() => {
    const counts = { all: activeMatchesPool.length };
    activeMatchesPool.forEach(m => {
      const d = m.date?.split('T')[0];
      if (d && d !== 'TBD') counts[d] = (counts[d] || 0) + 1;
    });
    return counts;
  });

  let groupsWithStandings = $derived.by(() => {
    const result = {};
    Object.keys(initialData.groups).forEach(name => {
      result[name] = initialData.groups[name]
        .map(code => liveStandings[code])
        .sort(compareTeams);
    });
    return result;
  });

  // --- KNOCKOUT DERIVATION ---
  let qualifiersData = $derived.by(() => {
    const top2 = {};
    const thirds = [];
    Object.keys(groupsWithStandings).forEach(name => {
      const g = groupsWithStandings[name];
      top2[`1${name}`] = g[0]?.code || 'TBD';
      top2[`2${name}`] = g[1]?.code || 'TBD';
      if (g[2]) {
        // We need to keep track of the origin group for the allocation lookup
        thirds.push({ ...g[2], originGroup: name });
      }
    });

    // Sort and pick best 8 third-place teams
    const sortedThirds = thirds.sort(compareTeams).slice(0, 8);
    
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

  let qualifiers = $derived(qualifiersData.slots);
  let isAllocationError = $derived(qualifiersData.hasError);

  // Map to store the rank (1-8) of the qualifying third-place teams
  let bestThirdsRankMap = $derived.by(() => {
    const thirds = [];
    Object.keys(groupsWithStandings).forEach(name => {
      if (groupsWithStandings[name][2]) thirds.push(groupsWithStandings[name][2]);
    });
    const sorted = thirds.sort(compareTeams).slice(0, 8);
    const map = {};
    sorted.forEach((t, i) => map[t.code] = i + 1);
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

  // --- VENUE SEARCH LOGIC ---
  let allTournamentMatches = $derived([
    ...matches.filter(m => m.id <= 72),
    ...r32Matches, ...r16Matches, ...qfMatches, ...sfMatches, ...thirdMatch, ...finalMatch
  ]);
</script>

<svelte:window 
  onclick={(e) => {
    if (isDateFilterOpen && dateFilterContainer && !dateFilterContainer.contains(e.target)) {
      isDateFilterOpen = false;
    }
    if (isVenueFilterOpen && venueFilterContainer && !venueFilterContainer.contains(e.target)) {
      isVenueFilterOpen = false;
    }
  }} 
  onkeydown={(e) => {
    if (e.key === 'Escape' && isDateFilterOpen) {
      isDateFilterOpen = false;
    }
    if (e.key === 'Escape' && isVenueFilterOpen) {
      isVenueFilterOpen = false;
    }
  }}
/>

{#snippet venueFilterUI()}
  {#if activeVenues.length > 2}
    <div class="filter-group">
      <label for="venue-select">{t.ui.select_venue}</label>
      <div class="custom-select-container" bind:this={venueFilterContainer}>
        <button 
          class="select-trigger" 
          aria-haspopup="listbox"
          aria-expanded={isVenueFilterOpen}
          onclick={() => isVenueFilterOpen = !isVenueFilterOpen}
        >
          {initialData.venues[selectedVenue] || t.ui.all_venues}
        </button>
        {#if isVenueFilterOpen}
          <div class="select-dropdown" role="listbox">
            <button 
              role="option"
              aria-selected={selectedVenue === null}
              class="select-option" 
              class:active-option={selectedVenue === null}
              onclick={() => { selectedVenue = null; isVenueFilterOpen = false; }}
            >
              {t.ui.all_venues}
            </button>
            {#each activeVenues.filter(v => v !== null) as code}
              {@const name = initialData.venues[code] || code}
              <button 
                role="option"
                aria-selected={selectedVenue === code}
                class="select-option" 
                class:active-option={selectedVenue === code}
                onclick={() => { selectedVenue = code; isVenueFilterOpen = false; }}
              >
                {name}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}
{/snippet}

{#snippet teamStatControls(matchId, team, teamKey, onUpdate)}
  <div class="team-input-group">
    <div class="team-info-wrapper">
      {#if team.code !== 'TBD'}
        <div 
          class="pixel-flag mini" 
          style="background-position: -{teamCodes.indexOf(team.code) * 31}px 0px;"
          aria-label="{t.teams[team.code]} flag"
        ></div>
      {/if}
      <span class="team-code">
        {team.code !== 'TBD' ? (t.teams[team.code] || team.code) : t.ui.tbd}
      </span>
    </div>

    {#if team.code !== 'TBD'}
      <div class="stat-control">
        <button type="button" class="stat-btn" onclick={() => onUpdate(matchId, teamKey, 'score', -1)}>-</button>
        <span class="stat-display">{team.score}</span>
        <button type="button" class="stat-btn" onclick={() => onUpdate(matchId, teamKey, 'score', 1)}>+</button>
      </div>
      <div class="match-cards-ui">
        <div class="card-control-item">
          <div class="pixel-card-icon yellow-card"></div>
          <div class="arcade-counter">
            <button type="button" class="stat-btn" onclick={() => onUpdate(matchId, teamKey, 'yellow_cards', -1)}>-</button>
            <span class="stat-count">{team.yellow_cards || 0}</span>
            <button type="button" class="stat-btn" onclick={() => onUpdate(matchId, teamKey, 'yellow_cards', 1)}>+</button>
          </div>
        </div>
        <div class="card-control-item">
          <div class="pixel-card-icon red-card"></div>
          <div class="arcade-counter">
            <button type="button" class="stat-btn" onclick={() => onUpdate(matchId, teamKey, 'red_cards', -1)}>-</button>
            <span class="stat-count">{team.red_cards || 0}</span>
            <button type="button" class="stat-btn" onclick={() => onUpdate(matchId, teamKey, 'red_cards', 1)}>+</button>
          </div>
        </div>
      </div>
    {/if}
  </div>
{/snippet}

{#snippet matchCard(match, onUpdate)}
  <div class="match-card">
    <div class="match-meta">{t.ui.match_label} #{match.id} // {formatDate(match.date)} // {initialData.venues[match.venue] || match.venue}</div>
    <div class="match-teams {match.id > 72 ? 'knockout-teams' : ''}">
      {@render teamStatControls(match.id, match.team1, 'team1', onUpdate)}
      <span class="vs">vs</span>
      {@render teamStatControls(match.id, match.team2, 'team2', onUpdate)}
    </div>

    {#if match.id > 72 && match.team1.code !== 'TBD' && match.team2.code !== 'TBD' && match.team1.score === match.team2.score}
      <div class="penalty-shootout">
        <p class="penalty-title">{t.status.penalties}</p>
        <div class="penalty-controls">
          <div class="stat-control">
            <button type="button" class="stat-btn" onclick={() => onUpdate(match.id, 'team1', 'penalties', -1)}>-</button>
            <span class="stat-display">{match.team1.penalties || 0}</span>
            <button type="button" class="stat-btn" onclick={() => onUpdate(match.id, 'team1', 'penalties', 1)}>+</button>
          </div>
          <span class="vs-pks">{t.status.pks}</span>
          <div class="stat-control">
            <button type="button" class="stat-btn" onclick={() => onUpdate(match.id, 'team2', 'penalties', -1)}>-</button>
            <span class="stat-display">{match.team2.penalties || 0}</span>
            <button type="button" class="stat-btn" onclick={() => onUpdate(match.id, 'team2', 'penalties', 1)}>+</button>
          </div>
        </div>
      </div>
    {/if}
  </div>
{/snippet}

{#snippet dateFilterUI()}
  {#if activeDates.length > 2}
    <div class="filter-group">
      <label for="date-select">{t.ui.filter_by}</label>
      <div class="custom-select-container" bind:this={dateFilterContainer}>
        <button 
          class="select-trigger" 
          aria-haspopup="listbox"
          aria-expanded={isDateFilterOpen}
          onclick={() => isDateFilterOpen = !isDateFilterOpen}
        >
          {formatShortDate(selectedDate)} [{activeMatchCounts[selectedDate]}]
        </button>
        {#if isDateFilterOpen}
          <div class="select-dropdown" role="listbox">
            {#each activeDates as date}
              <button 
                role="option"
                aria-selected={selectedDate === date}
                class="select-option" 
                class:active-option={selectedDate === date}
                onclick={() => { selectedDate = date; isDateFilterOpen = false; }}
              >
                {formatShortDate(date)} [{activeMatchCounts[date]}]
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}
{/snippet}

{#snippet globalFiltersUI()}
  {#if activeDates.length > 2 || activeVenues.length > 2}
    <div class="arcade-filters">
      {@render dateFilterUI()}
      {@render venueFilterUI()}
    </div>
  {/if}
{/snippet}

<div class="app-container">
  <header class="arcade-header">
    <h1>RETRO CUP 26</h1>
    <p class="subtitle">{t.ui.tracker} v1.0 // {t.ui.ready}</p>
    <div class="lang-switcher">
      <button class:active-lang={locale === 'en'} onclick={() => locale = 'en'}>EN</button>
      <button class:active-lang={locale === 'pt'} onclick={() => locale = 'pt'}>PT</button>
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
      <button class="reset-btn-nav" onclick={resetData}>
        [ {t.ui.reset} ]
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

        {#each activeMatchesPool.filter(m => 
          (selectedDate === 'all' || m.date?.startsWith(selectedDate)) && 
          (!selectedVenue || m.venue === selectedVenue)
        ) as match (match.id)}
          {@render matchCard(match, updateMatchData)}
        {/each}
      </div>
    {:else}
      <div class="standings-container">
        {#each Object.entries(groupsWithStandings) as [groupName, teams]}
          <div class="group-standings">
            <h3 class="group-title">[ {t.standings.group} {groupName} ]</h3>
            <table class="standings-table">
              <thead>
                <tr>
                  <th>{t.standings.pos}</th>
                  <th>{t.standings.team}</th>
                  <th>{t.standings.mp}</th>
                  <th>{t.standings.wdl}</th>
                  <th>{t.standings.gf}</th>
                  <th>{t.standings.ga}</th>
                  <th>{t.standings.gd}</th>
                  <th>{t.standings.pts}</th>
                </tr>
              </thead>
              <tbody>
                {#each teams as team, i}
                  {@const isQualified = Object.values(qualifiers).includes(team.code)}
                  <tr class="position-{i + 1} {isQualified ? 'clinched-row' : ''}">
                    <td class="position">{i + 1}</td>
                    <td class="team-name">
                      <div 
                        class="pixel-flag mini" 
                        style="background-position: -{teamCodes.indexOf(team.code) * 31}px 0px;"
                        aria-label="{t.teams[team.code]} flag"></div>
                      <span>{team.name || team.code}</span>
                      {#if bestThirdsRankMap[team.code]}<sup class="third-rank-indicator">{bestThirdsRankMap[team.code]}</sup>{/if}
                    </td>
                    <td>{team.mp}</td>
                    <td>{team.w}-{team.d}-{team.l}</td>
                    <td>{team.gf}</td>
                    <td>{team.ga}</td>
                    <td>{team.gd > 0 ? '+' : ''}{team.gd}</td>
                    <td class="points-cell">{team.pts}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
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