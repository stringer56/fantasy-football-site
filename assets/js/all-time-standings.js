(() => {
  const table = document.querySelector("[data-all-time-table]");
  if (!table) return;
  const body = table.tBodies[0];
  const buttons = [...table.querySelectorAll("button[data-sort]")];
  let active = "pct";
  let direction = "descending";

  const compare = (a, b, key, type) => {
    const left = a.dataset[key] || "";
    const right = b.dataset[key] || "";
    if (type === "number") return Number(left) - Number(right);
    return left.localeCompare(right);
  };

  const sortRows = (button) => {
    const key = button.dataset.sort;
    const type = button.dataset.type;
    direction = active === key && direction === "descending" ? "ascending" : "descending";
    active = key;
    const multiplier = direction === "ascending" ? 1 : -1;
    const rows = [...body.rows].sort((a, b) => {
      const primary = compare(a, b, key, type) * multiplier;
      if (primary) return primary;
      const wins = (Number(b.dataset.wins) - Number(a.dataset.wins));
      if (wins) return wins;
      return a.dataset.name.localeCompare(b.dataset.name);
    });
    rows.forEach((row, index) => {
      row.querySelector("[data-rank]").textContent = String(index + 1);
      body.appendChild(row);
    });
    buttons.forEach((item) => item.closest("th").setAttribute("aria-sort", item === button ? direction : "none"));
  };

  buttons.forEach((button) => button.addEventListener("click", () => sortRows(button)));
})();
