<script>
  import PixelFlag from './PixelFlag.svelte';
  
  let { match, t, teamCodes, venues, onUpdate, formatDate, isReadOnly = false } = $props();

  function handleStat(teamKey, statKey, delta) {
    if (isReadOnly) return;
    onUpdate(match.id, teamKey, statKey, delta);
  }
</script>

<div class="match-card">
  <div class="match-meta">
    {t.ui.match_label} #{match.id} // {formatDate(match.date)} // {venues[match.venue] || match.venue}
  </div>
  
  <div class="match-teams {match.id > 72 ? 'knockout-teams' : ''}">
    <!-- Team 1 -->
    <div class="team-input-group">
      <div class="team-info-wrapper">
        <PixelFlag code={match.team1.code} {teamCodes} alt={t.teams[match.team1.code]} />
        <div class="team-name-container">
          <span class="team-code full-name">{match.team1.code !== 'TBD' ? (t.teams[match.team1.code] || match.team1.code) : t.ui.tbd}</span>
          <span class="team-code short-name">{match.team1.code}</span>
        </div>
      </div>

      {#if match.team1.code !== 'TBD'}
        <div class="stat-control">
          <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'score', -1)} disabled={isReadOnly}>-</button>
          <span class="stat-display">{match.team1.score}</span>
          <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'score', 1)} disabled={isReadOnly}>+</button>
        </div>
        <div class="match-cards-ui">
          <div class="card-control-item">
            <div class="pixel-card-icon yellow-card"></div>
            <div class="arcade-counter">
              <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'yellow_cards', -1)} disabled={isReadOnly}>-</button>
              <span class="stat-count">{match.team1.yellow_cards || 0}</span>
              <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'yellow_cards', 1)} disabled={isReadOnly}>+</button>
            </div>
          </div>
          <div class="card-control-item">
            <div class="pixel-card-icon red-card"></div>
            <div class="arcade-counter">
              <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'red_cards', -1)} disabled={isReadOnly}>-</button>
              <span class="stat-count">{match.team1.red_cards || 0}</span>
              <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'red_cards', 1)} disabled={isReadOnly}>+</button>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <span class="vs">vs</span>

    <!-- Team 2 -->
    <div class="team-input-group">
      <div class="team-info-wrapper">
        <PixelFlag code={match.team2.code} {teamCodes} alt={t.teams[match.team2.code]} />
        <div class="team-name-container">
          <span class="team-code full-name">{match.team2.code !== 'TBD' ? (t.teams[match.team2.code] || match.team2.code) : t.ui.tbd}</span>
          <span class="team-code short-name">{match.team2.code}</span>
        </div>
      </div>

      {#if match.team2.code !== 'TBD'}
        <div class="stat-control">
          <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'score', -1)} disabled={isReadOnly}>-</button>
          <span class="stat-display">{match.team2.score}</span>
          <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'score', 1)} disabled={isReadOnly}>+</button>
        </div>
        <div class="match-cards-ui">
          <div class="card-control-item">
            <div class="pixel-card-icon yellow-card"></div>
            <div class="arcade-counter">
              <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'yellow_cards', -1)} disabled={isReadOnly}>-</button>
              <span class="stat-count">{match.team2.yellow_cards || 0}</span>
              <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'yellow_cards', 1)} disabled={isReadOnly}>+</button>
            </div>
          </div>
          <div class="card-control-item">
            <div class="pixel-card-icon red-card"></div>
            <div class="arcade-counter">
              <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'red_cards', -1)} disabled={isReadOnly}>-</button>
              <span class="stat-count">{match.team2.red_cards || 0}</span>
              <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'red_cards', 1)} disabled={isReadOnly}>+</button>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>

  {#if match.id > 72 && match.team1.code !== 'TBD' && match.team2.code !== 'TBD' && match.team1.score === match.team2.score}
    <div class="penalty-shootout">
      <p class="penalty-title">{t.status.penalties}</p>
      <div class="penalty-controls">
        <div class="stat-control">
          <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'penalties', -1)} disabled={isReadOnly}>-</button>
          <span class="stat-display">{match.team1.penalties || 0}</span>
          <button type="button" class="stat-btn" onclick={() => handleStat('team1', 'penalties', 1)} disabled={isReadOnly}>+</button>
        </div>
        <span class="vs-pks">{t.status.pks}</span>
        <div class="stat-control">
          <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'penalties', -1)} disabled={isReadOnly}>-</button>
          <span class="stat-display">{match.team2.penalties || 0}</span>
          <button type="button" class="stat-btn" onclick={() => handleStat('team2', 'penalties', 1)} disabled={isReadOnly}>+</button>
        </div>
      </div>
    </div>
  {/if}
</div>