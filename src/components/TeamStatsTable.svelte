<script>
  import PixelFlag from './PixelFlag.svelte';

  let { stats, t, teamCodes } = $props();

  let sortColumn = $state('pts');
  let sortDirection = $state('desc');

  function toggleSort(col) {
    if (sortColumn === col) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = col;
      sortDirection = (col === 'name' || col === 'ga' || col === 'yc' || col === 'rc') ? 'asc' : 'desc';
    }
  }

  let sortedStats = $derived.by(() => {
    return [...stats].sort((a, b) => {
      let valA = a[sortColumn];
      let valB = b[sortColumn];

      if (sortColumn === 'name') {
        const nameA = t.teams[a.code] || a.code;
        const nameB = t.teams[b.code] || b.code;
        const res = nameA.localeCompare(nameB);
        return sortDirection === 'asc' ? res : -res;
      }

      if (valA !== valB) {
        const diff = Number(valA || 0) - Number(valB || 0);
        return sortDirection === 'asc' ? diff : -diff;
      }

      // Secondary tie-breaker
      if (b.pts !== a.pts) return b.pts - a.pts;
      if (b.gd !== a.gd) return b.gd - a.gd;
      if (b.gf !== a.gf) return b.gf - a.gf;
      const nameA = t.teams[a.code] || a.code;
      const nameB = t.teams[b.code] || b.code;
      return nameA.localeCompare(nameB);
    });
  });
</script>

<div class="team-stats-container">
  <h2 class="section-title">[ {t.stats.title} ]</h2>
  <div class="table-scroll-wrapper">
    <table class="standings-table stats-table">
      <thead>
        <tr>
          <th class="pos-col">#</th>
          <th class="sortable-th text-left" onclick={() => toggleSort('name')}>
            {t.stats.team} <span class="sort-icon">{sortColumn === 'name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="sortable-th" onclick={() => toggleSort('mp')}>
            {t.stats.mp} <span class="sort-icon">{sortColumn === 'mp' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="sortable-th" onclick={() => toggleSort('pts')}>
            {t.stats.pts} <span class="sort-icon">{sortColumn === 'pts' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="non-sortable">{t.stats.wdl}</th>
          <th class="sortable-th" onclick={() => toggleSort('gf')}>
            {t.stats.gf} <span class="sort-icon">{sortColumn === 'gf' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="sortable-th" onclick={() => toggleSort('ga')}>
            {t.stats.ga} <span class="sort-icon">{sortColumn === 'ga' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="sortable-th" onclick={() => toggleSort('gd')}>
            {t.stats.gd} <span class="sort-icon">{sortColumn === 'gd' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="sortable-th" onclick={() => toggleSort('yc')}>
            {t.stats.yc} <span class="sort-icon">{sortColumn === 'yc' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
          <th class="sortable-th" onclick={() => toggleSort('rc')}>
            {t.stats.rc} <span class="sort-icon">{sortColumn === 'rc' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {#each sortedStats as team, i (team.code)}
          <tr>
            <td class="position">{i + 1}</td>
            <td class="team-name text-left">
              <PixelFlag 
                code={team.code} 
                {teamCodes} 
                mini={true} 
                alt="{t.teams[team.code] || team.code} flag" 
              />
              <span class="full-name">{t.teams[team.code] || team.code}</span>
              <span class="short-name">{team.code}</span>
            </td>
            <td>{team.mp}</td>
            <td class="points-cell">{team.pts}</td>
            <td>{team.w}-{team.d}-{team.l}</td>
            <td>{team.gf}</td>
            <td>{team.ga}</td>
            <td class="{team.gd > 0 ? 'gd-positive' : team.gd < 0 ? 'gd-negative' : ''}">
              {team.gd > 0 ? '+' : ''}{team.gd}
            </td>
            <td>{team.yc}</td>
            <td>{team.rc}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>
