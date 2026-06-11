<script>
  /**
   * Reusable Filter Select Component for the Retro Cup 26 simulator.
   * Uses Svelte 5 Runes for reactivity.
   */
  let { label, options, value = $bindable(), placeholder } = $props();
  let isOpen = $state(false);

  // Generate a unique ID for this instance to associate the label with the button
  const selectId = `select-${Math.random().toString(36).slice(2, 6)}`;

  function toggle() {
    isOpen = !isOpen;
  }

  function select(optId) {
    value = optId;
    isOpen = false;
  }

  // Close dropdown when clicking outside
  function handleOutsideClick(event) {
    if (isOpen && !event.target.closest('.custom-select-container')) {
      isOpen = false;
    }
  }
</script>

<svelte:window onclick={handleOutsideClick} />

<div class="filter-group">
  <label for={selectId}>{label}</label>
  <div class="custom-select-container" class:is-open={isOpen}>
    <button 
      id={selectId}
      class="select-trigger" 
      onclick={toggle} 
      type="button"
      aria-haspopup="listbox"
      aria-expanded={isOpen}
    >
      {options.find(o => o.id === value)?.label || placeholder}
    </button>
    
    {#if isOpen}
      <div class="select-dropdown">
        {#each options as opt}
          <button 
            class="select-option" 
            class:active-option={value === opt.id}
            onclick={() => select(opt.id)}
            type="button"
          >
            {opt.label}
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>
