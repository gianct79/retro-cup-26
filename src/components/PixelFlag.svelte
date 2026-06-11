<script>
  /**
   * Handles the 8-bit spritesheet logic for flags.
   */
  let { code, teamCodes, mini = false, alt = "" } = $props();

  const index = $derived(teamCodes.indexOf(code));
</script>

{#if code && code !== 'TBD'}
  <div 
    class="pixel-flag {mini ? 'mini' : ''}" 
    style="--flag-index: {index >= 0 ? index : 0};"
    aria-label={alt}
  ></div>
{/if}