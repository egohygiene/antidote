(() => {
  "use strict";

  const catalogUrl = document.body.dataset.catalogUrl;
  if (!catalogUrl) {
    return;
  }

  const setFields = (name, value) => {
    for (const field of document.querySelectorAll(`[data-site-field="${name}"]`)) {
      field.textContent = value;
    }
  };

  fetch(catalogUrl, { credentials: "same-origin" })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`site catalog request failed: ${response.status}`);
      }
      return response.json();
    })
    .then((catalog) => {
      const slots = new Map(catalog.slots.map((slot) => [slot.id, slot]));
      const paper = slots.get("paper");
      const magazine = slots.get("magazine");
      if (paper?.version) {
        setFields("paper-version", paper.version);
      }
      if (magazine?.status) {
        setFields("magazine-status", magazine.status);
      }
      if (catalog.source_revision) {
        setFields("source-revision", catalog.source_revision.slice(0, 12));
      }
    })
    .catch(() => {
      // Committed text is complete without JavaScript; hydration is optional.
    });
})();
