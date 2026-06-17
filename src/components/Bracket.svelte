<script>
  let { rounds, t, teamCodes } = $props();

  let containerWidth = $state(0);
  let contentWidth = $state(0);
  let isScrollable = $derived(containerWidth > 0 && contentWidth > containerWidth + 10);

  // Rounds should be an array of objects: { label: string, matches: Array }
  const getFlagIndex = (code) => teamCodes.indexOf(code);

  function isWinner(match, teamCode) {
    if (!match.played || !teamCode || teamCode === 'TBD') return false;
    const s1 = match.team1.score + (match.team1.penalties || 0);
    const s2 = match.team2.score + (match.team2.penalties || 0);
    if (teamCode === match.team1.code) return s1 > s2;
    if (teamCode === match.team2.code) return s2 > s1;
    return false;
  }
</script>

<div 
  class="bracket-scroll-container" 
  class:can-scroll={isScrollable}
  title={isScrollable ? t.ui.swipe_to_view : ""} 
  bind:clientWidth={containerWidth}
>
  <div class="bracket-wrapper" bind:clientWidth={contentWidth}>
    {#each rounds as round, rIdx (round.label)}
      <div class="bracket-column">
        <h3 class="section-title" style="font-size: 8px; border: none; margin-bottom: 10px;">
          {round.label}
        </h3>
        <div class="bracket-round" class:is-final={rIdx === rounds.length - 1}>
          {#each round.matches as match}
            <div class="bracket-match-node" class:match-played={match.played}>
              <div class="bracket-team" class:winner={isWinner(match, match.team1.code)}>
                <div style="display: flex; align-items: center; gap: 4px;">
                  <div class="pixel-flag micro" 
                       style="--flag-index: {getFlagIndex(match.team1.code)}">
                  </div>
                  <span>{match.team1.code}</span>
                </div>
                <span class="bracket-score">{match.played ? match.team1.score : '-'}</span>
              </div>

              <div class="bracket-team" class:winner={isWinner(match, match.team2.code)}>
                <div style="display: flex; align-items: center; gap: 4px;">
                  <div class="pixel-flag micro" 
                       style="--flag-index: {getFlagIndex(match.team2.code)}">
                  </div>
                  <span>{match.team2.code}</span>
                </div>
                <span class="bracket-score">{match.played ? match.team2.score : '-'}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  </div>
</div>

{#if isScrollable}
  <p class="subtitle" style="text-align: center; margin-top: 10px; font-size: 8px;">
    &lt;&lt; {t.ui.swipe_to_view} &gt;&gt;
  </p>
{/if}