/**
 * initCombo(ids, selectedValue)
 *
 * ids = {
 *   combo      : wrapper div id
 *   trigger    : trigger div id
 *   dropdown   : dropdown div id
 *   display    : inner display div id
 *   hidden     : hidden input id
 *   search     : search input id
 *   options    : options list div id
 *   noResults  : no-results div id
 * }
 * selectedValue : optional string — pre-select the option with this data-value
 */
function initCombo(ids, selectedValue) {
  const combo      = document.getElementById(ids.combo);
  const trigger    = document.getElementById(ids.trigger);
  const dropdown   = document.getElementById(ids.dropdown);
  const display    = document.getElementById(ids.display);
  const hidden     = document.getElementById(ids.hidden);
  const searchBox  = document.getElementById(ids.search);
  const optionList = document.getElementById(ids.options);
  const noRes      = document.getElementById(ids.noResults);

  if (!trigger) return;

  const allOptions = Array.from(optionList.querySelectorAll('.combo-option'));

  function openDropdown() {
    trigger.classList.add('open');
    trigger.setAttribute('aria-expanded', 'true');
    dropdown.classList.add('open');
    searchBox.value = '';
    filterOptions('');
    searchBox.focus();
  }

  function closeDropdown() {
    trigger.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
    dropdown.classList.remove('open');
  }

  function selectOption(opt) {
    const val      = opt.dataset.value;
    const name     = opt.dataset.name;
    const role     = opt.dataset.role;
    const initials = opt.dataset.initials;
    const color    = opt.querySelector('.combo-avatar').style.background;

    hidden.value = val;

    if (val === '') {
      display.innerHTML = '<span class="placeholder-text">Seleccionar profesional</span>';
    } else {
      display.innerHTML =
        `<div class="combo-avatar" style="background:${color};width:26px;height:26px;font-size:.65rem;">${initials}</div>` +
        `<span style="font-size:.875rem;color:#344767;">${name}</span>` +
        `<span style="font-size:.68rem;color:#7b809a;background:#f0f0f0;border-radius:.35rem;padding:.1rem .4rem;">${role}</span>`;
    }

    allOptions.forEach(o => o.classList.toggle('selected', o === opt));
    closeDropdown();
  }

  function filterOptions(q) {
    let visible = 0;
    allOptions.forEach(opt => {
      const match = (opt.dataset.search || '').includes(q.toLowerCase());
      opt.style.display = match ? '' : 'none';
      if (match) visible++;
    });
    noRes.style.display = visible === 0 ? 'block' : 'none';
  }

  trigger.addEventListener('click', () => {
    dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
  });

  trigger.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openDropdown(); }
    if (e.key === 'Escape') closeDropdown();
  });

  searchBox.addEventListener('input', () => filterOptions(searchBox.value));

  optionList.addEventListener('click', e => {
    const opt = e.target.closest('.combo-option');
    if (opt) selectOption(opt);
  });

  document.addEventListener('click', e => {
    if (combo && !combo.contains(e.target)) closeDropdown();
  });

  // Pre-select if a value was provided
  if (selectedValue !== undefined && selectedValue !== null && selectedValue !== '') {
    const opt = allOptions.find(o => o.dataset.value === String(selectedValue));
    if (opt) selectOption(opt);
  }
}
