(() => {
  const cards = [...document.querySelectorAll('.person-card')];
  const search = document.querySelector('#people-search');
  const status = document.querySelector('#people-status');
  const dataset = document.querySelector('#people-dataset');
  const organization = document.querySelector('#people-organization');
  const year = document.querySelector('#people-year');
  const count = document.querySelector('#people-result-count');
  const empty = document.querySelector('#people-empty');

  const normalize = (value) => (value || '').trim().toLowerCase();
  const includesToken = (haystack, needle) => !needle || (haystack || '').split('|').includes(needle);

  function applyFilters() {
    const query = normalize(search?.value);
    const wantedStatus = normalize(status?.value);
    const wantedDataset = normalize(dataset?.value);
    const wantedOrganization = normalize(organization?.value);
    const wantedYear = normalize(year?.value);
    let visible = 0;

    for (const card of cards) {
      const matches = (
        (!query || card.dataset.search.includes(query)) &&
        includesToken(card.dataset.statuses, wantedStatus) &&
        includesToken(card.dataset.datasets, wantedDataset) &&
        includesToken(card.dataset.organizations, wantedOrganization) &&
        (!wantedYear || (card.dataset.years || '').split('|').includes(wantedYear))
      );
      card.hidden = !matches;
      if (matches) visible += 1;
    }

    if (count) count.textContent = `${visible.toLocaleString()} of ${cards.length.toLocaleString()} people`;
    if (empty) empty.hidden = visible !== 0;
  }

  for (const control of [search, status, dataset, organization, year]) {
    control?.addEventListener(control.tagName === 'SELECT' ? 'change' : 'input', applyFilters);
  }
  applyFilters();
})();
