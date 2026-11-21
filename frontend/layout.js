// Shared room layout and drawing code for index.html (students) and admin.html (admin).
// Change the table IDs here only, and both pages follow.
//
// IDs match the detector (studyspot-agent/main.py, layout()):
//   1-3   group room tables
//   4-15  study tables, left to right, top to bottom (4 x 3)
//   16-23 wall desks, top to bottom (the detector currently watches 16-21)
// Seat counts shown on the cards come from the data, not from here.

const TOPA = (() => {
  const GROUP_ROOMS = [
    { id: 1, label: "Group Room 1", short: "G1", seats: 5 },
    { id: 2, label: "Group Room 2", short: "G2", seats: 5 },
    { id: 3, label: "Group Room 3", short: "G3", seats: 3 }
  ];
  const STUDY_TABLES = Array.from({ length: 12 }, (_, i) =>
    ({ id: 4 + i, label: "T" + (i + 1), short: "T" + (i + 1), seats: 6 }));
  const WALL_DESKS = Array.from({ length: 8 }, (_, i) =>
    ({ id: 16 + i, label: "D" + (i + 1), short: "D" + (i + 1), seats: 1 }));
  const ALL_TABLES = [...GROUP_ROOMS, ...STUDY_TABLES, ...WALL_DESKS];

  const STATUS_TEXT = {
    free: "Empty", partly: "Semi-occupied", full: "Occupied",
    items: "Items only", unknown: "No data"
  };

  // IDs that have appeared in any data so far. Once data has arrived, cards for
  // IDs that never appear (e.g. desks the detector does not watch) are hidden.
  const seen = new Set();
  let anyData = false;

  function floorHTML() {
    return `
      <div class="floor">
        <div class="shelf" title="Bookshelf"></div>
        <div class="rooms" data-area="rooms"></div>
        <div class="print">Print · Copy</div>
        <div class="study-wrap">
          <div class="area-label">Study tables</div>
          <div class="study" data-area="study"></div>
        </div>
        <div class="desks-wrap">
          <div class="area-label">Wall desks</div>
          <div class="desks" data-area="desks"></div>
        </div>
        <div class="help">Help desk</div>
      </div>`;
  }

  function makeCard(t) {
    const card = document.createElement("div");
    card.dataset.tableId = t.id;
    card.className = "card unknown";
    card.innerHTML = '<div class="name"></div><div class="seats"></div>' +
                     '<div class="count"></div><div class="state">No data</div><div class="timer"></div>';
    card.querySelector(".name").textContent = t.short;
    return card;
  }

  // Draw the empty room inside `container`
  function buildFloor(container) {
    container.innerHTML = floorHTML();
    const rooms = container.querySelector('[data-area="rooms"]');
    GROUP_ROOMS.forEach(t => {
      const room = document.createElement("div");
      room.className = "room";
      const label = document.createElement("div");
      label.className = "area-label";
      label.textContent = t.label;
      room.append(label, makeCard(t));
      rooms.appendChild(room);
    });
    const study = container.querySelector('[data-area="study"]');
    STUDY_TABLES.forEach(t => study.appendChild(makeCard(t)));
    const desks = container.querySelector('[data-area="desks"]');
    WALL_DESKS.forEach(t => desks.appendChild(makeCard(t)));
  }

  function formatTimer(sec) {
    if (!sec) return "";
    return sec < 60 ? Math.round(sec) + " s" : Math.floor(sec / 60) + " min";
  }

  // rows: [{table_id, seats, people, status, items_seconds?}]
  // Updates the cards in `container` and returns the summary counts.
  function renderTables(container, rows) {
    const byId = {};
    rows.forEach(r => { byId[r.table_id] = r; seen.add(r.table_id); });
    if (rows.length) anyData = true;

    const counts = { free: 0, partly: 0, full: 0, items: 0, people: 0 };
    ALL_TABLES.forEach(t => {
      const card = container.querySelector('[data-table-id="' + t.id + '"]');
      if (!card) return;
      const r = byId[t.id];
      const status = r && STATUS_TEXT[r.status] ? r.status : "unknown";
      const seats = r && r.seats ? r.seats : t.seats;
      const people = r && typeof r.people === "number" ? r.people : 0;

      card.className = "card " + status + (anyData && !seen.has(t.id) ? " hidden" : "");
      card.title = t.label + ": " + STATUS_TEXT[status] + (r ? " (" + people + "/" + seats + ")" : "");
      card.querySelector(".count").textContent =
        r ? people + " / " + seats + (seats === 1 ? " seat" : " seats") : "";
      card.querySelector(".state").textContent = STATUS_TEXT[status];
      card.querySelector(".timer").textContent =
        status === "items" && r.items_seconds ? "⏱ " + formatTimer(r.items_seconds) : "";

      const seatsEl = card.querySelector(".seats");
      seatsEl.innerHTML = "";
      for (let i = 0; i < seats; i++) {
        const d = document.createElement("span");
        d.className = "seat" + (r && i < people ? " taken" : "");
        seatsEl.appendChild(d);
      }

      if (counts[status] !== undefined) counts[status]++;
      counts.people += people;
    });
    return counts;
  }

  // Fill the summary cards (elements with these ids, if present)
  function renderSummary(counts, peopleSoFar) {
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set("sum-free", counts.free);
    set("sum-partly", counts.partly);
    set("sum-full", counts.full);
    set("sum-items", counts.items);
    set("sum-people-now", counts.people);
    set("sum-people-today", typeof peopleSoFar === "number" ? peopleSoFar : "–");
  }

  return { GROUP_ROOMS, STUDY_TABLES, WALL_DESKS, ALL_TABLES, STATUS_TEXT,
           buildFloor, renderTables, renderSummary };
})();
