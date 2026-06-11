<script>
  /**
   * Handles the 8-bit spritesheet logic for flags.
   */
  let { code, teamCodes, mini = false, alt = "" } = $props();

  const spriteWidth = $derived(mini ? 31 : 62);
  const index = $derived(teamCodes.indexOf(code));
  const position = $derived(index >= 0 ? -(index * spriteWidth) : 0);
</script>

{#if code && code !== 'TBD'}
  <div 
    class="pixel-flag {mini ? 'mini' : ''}" 
    style="background-position: {position}px 0px;"
    aria-label={alt}
  ></div>
{/if}