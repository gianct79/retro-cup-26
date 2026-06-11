<script>
  import PixelFlag from './PixelFlag.svelte';
  
  let { groupName, teams, t, teamCodes, qualifiers, bestThirdsRankMap } = $props();

  const qualifierList = $derived(Object.values(qualifiers));
</script>

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
        {@const isQualified = qualifierList.includes(team.code)}
        <tr class="position-{i + 1} {isQualified ? 'clinched-row' : ''}">
          <td class="position">{i + 1}</td>
          <td class="team-name">
            <PixelFlag 
              code={team.code} 
              {teamCodes} 
              mini={true} 
              alt="{team.name || team.code} flag" 
            />
            <span class="full-name">{team.name || team.code}</span>
            <span class="short-name">{team.code}</span>
            {#if bestThirdsRankMap[team.code]}
              <sup class="third-rank-indicator">{bestThirdsRankMap[team.code]}</sup>
            {/if}
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