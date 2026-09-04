(function () {
  "use strict";

  const root = document.querySelector("[data-power-chart]");
  const source = document.getElementById("power-ranking-history-data");
  if (!root || !source) return;

  let history;
  try { history = JSON.parse(source.textContent); } catch (_error) { return; }
  const franchises = (history.franchises || []).filter((team) => team.weeks && team.weeks.length);
  if (!franchises.length) return;

  const svg = root.querySelector("[data-power-svg]");
  const legend = root.querySelector("[data-power-legend]");
  const tooltip = root.querySelector("[data-power-tooltip]");
  const selectionText = root.querySelector("[data-power-selection]");
  const select = root.querySelector("[data-power-select]");
  const palette = ["#b91c1c", "#1d4ed8", "#047857", "#7e22ce", "#b45309", "#0e7490", "#be185d", "#4d7c0f", "#4338ca", "#c2410c", "#0369a1", "#6b21a8"];
  const mobile = window.matchMedia("(max-width: 560px)").matches;
  const selected = new Set((mobile ? franchises.filter((team) => team.current_rank <= 3) : franchises).map((team) => team.franchise_id));
  const ns = "http://www.w3.org/2000/svg";

  franchises.forEach((team, index) => {
    team.chartColor = team.primary_color || palette[index % palette.length];
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.franchise = team.franchise_id;
    button.setAttribute("aria-pressed", selected.has(team.franchise_id) ? "true" : "false");
    button.innerHTML = `<span style="--series-color:${team.chartColor}"></span>${team.short_name || team.display_name}`;
    button.addEventListener("click", () => {
      if (selected.has(team.franchise_id)) selected.delete(team.franchise_id); else selected.add(team.franchise_id);
      render();
    });
    legend.appendChild(button);
  });

  function make(name, attrs, text) {
    const node = document.createElementNS(ns, name);
    Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, String(value)));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function movementText(value) {
    if (value === null || value === undefined || value === 0) return "—";
    return value > 0 ? `▲ ${value}` : `▼ ${Math.abs(value)}`;
  }

  function showTooltip(event, team, point) {
    tooltip.innerHTML = `<strong>${team.display_name} · Week ${point.week}</strong><span>Rank #${point.rank}</span><span>Previous: ${point.previous_rank ? `#${point.previous_rank}` : "—"}</span><span>Movement: ${movementText(point.movement)}</span><span>Average manager rank: ${point.average_rank}</span><span>First-place votes: ${point.first_place_votes}</span>`;
    tooltip.hidden = false;
    const canvas = root.querySelector(".power-chart__canvas").getBoundingClientRect();
    const target = event.currentTarget.getBoundingClientRect();
    tooltip.style.left = `${Math.max(8, Math.min(canvas.width - tooltip.offsetWidth - 8, target.left - canvas.left + target.width / 2))}px`;
    tooltip.style.top = `${Math.max(8, target.top - canvas.top - tooltip.offsetHeight - 10)}px`;
  }

  function hideTooltip() { tooltip.hidden = true; }

  function render() {
    const canvas = root.querySelector(".power-chart__canvas");
    const width = Math.max(300, Math.floor(canvas.clientWidth));
    const height = width <= 560 ? 360 : 500;
    const margin = { top: 26, right: 22, bottom: 54, left: 58 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const allWeeks = [...new Set(franchises.flatMap((team) => team.weeks.map((point) => point.week)))].sort((a, b) => a - b);
    const minWeek = Math.min(...allWeeks);
    const maxWeek = Math.max(...allWeeks);
    const x = (week) => margin.left + (maxWeek === minWeek ? innerWidth / 2 : ((week - minWeek) / (maxWeek - minWeek)) * innerWidth);
    const y = (rank) => margin.top + ((rank - 1) / 11) * innerHeight;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.replaceChildren();
    svg.appendChild(make("title", {}, "2026 manager Power Ranking movement"));
    svg.appendChild(make("desc", {}, "Each selected franchise is plotted by finalized weekly rank, with rank one at the top and rank twelve at the bottom."));

    for (let rank = 1; rank <= 12; rank += 1) {
      svg.appendChild(make("line", { x1: margin.left, x2: width - margin.right, y1: y(rank), y2: y(rank), class: "power-chart__grid" }));
      svg.appendChild(make("text", { x: margin.left - 12, y: y(rank) + 4, "text-anchor": "end", class: "power-chart__tick" }, `#${rank}`));
    }
    allWeeks.forEach((week) => {
      svg.appendChild(make("line", { x1: x(week), x2: x(week), y1: margin.top, y2: height - margin.bottom, class: "power-chart__week-line" }));
      svg.appendChild(make("text", { x: x(week), y: height - margin.bottom + 24, "text-anchor": "middle", class: "power-chart__tick" }, `W${week}`));
    });
    svg.appendChild(make("text", { x: width / 2, y: height - 10, "text-anchor": "middle", class: "power-chart__axis-title" }, "Finalized week"));
    svg.appendChild(make("text", { x: 16, y: height / 2, transform: `rotate(-90 16 ${height / 2})`, "text-anchor": "middle", class: "power-chart__axis-title" }, "Power rank"));

    franchises.forEach((team) => {
      const active = selected.has(team.franchise_id);
      const group = make("g", { class: `power-chart__series${active ? " is-active" : ""}`, "data-series": team.franchise_id, style: `--series-color:${team.chartColor}` });
      if (active) {
        let segment = [];
        team.weeks.forEach((point, index) => {
          if (segment.length && point.week !== segment[segment.length - 1].week + 1) {
            group.appendChild(make("polyline", { points: segment.map((item) => `${x(item.week)},${y(item.rank)}`).join(" "), class: "power-chart__line" }));
            segment = [];
          }
          segment.push(point);
          if (index === team.weeks.length - 1 && segment.length) group.appendChild(make("polyline", { points: segment.map((item) => `${x(item.week)},${y(item.rank)}`).join(" "), class: "power-chart__line" }));
        });
        team.weeks.forEach((point) => {
          const circle = make("circle", { cx: x(point.week), cy: y(point.rank), r: 5, class: "power-chart__point", tabindex: "0", role: "img", "aria-label": `${team.display_name}, Week ${point.week}, rank ${point.rank}, movement ${movementText(point.movement)}, average manager rank ${point.average_rank}, ${point.first_place_votes} first-place votes` });
          circle.addEventListener("mouseenter", (event) => showTooltip(event, team, point));
          circle.addEventListener("mouseleave", hideTooltip);
          circle.addEventListener("focus", (event) => showTooltip(event, team, point));
          circle.addEventListener("blur", hideTooltip);
          group.appendChild(circle);
        });
      }
      svg.appendChild(group);
      const button = legend.querySelector(`[data-franchise="${team.franchise_id}"]`);
      if (button) button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    const names = franchises.filter((team) => selected.has(team.franchise_id)).map((team) => team.short_name || team.display_name);
    selectionText.textContent = names.length ? `Showing ${names.length}: ${names.join(", ")}` : "No franchise lines selected. Use the legend or controls to add one.";
  }

  root.addEventListener("mouseover", (event) => {
    const series = event.target.closest("[data-series]");
    if (!series) return;
    svg.querySelectorAll("[data-series]").forEach((node) => node.classList.toggle("is-muted", node !== series));
  });
  root.addEventListener("mouseout", () => svg.querySelectorAll("[data-series]").forEach((node) => node.classList.remove("is-muted")));
  root.querySelector('[data-power-action="all"]').addEventListener("click", () => { franchises.forEach((team) => selected.add(team.franchise_id)); render(); });
  root.querySelector('[data-power-action="top"]').addEventListener("click", () => { selected.clear(); franchises.filter((team) => team.current_rank <= 3).forEach((team) => selected.add(team.franchise_id)); render(); });
  root.querySelector('[data-power-action="clear"]').addEventListener("click", () => { selected.clear(); render(); });
  root.querySelector('[data-power-action="add"]').addEventListener("click", () => { if (select.value) selected.add(select.value); render(); });
  let resizeTimer;
  window.addEventListener("resize", () => { window.clearTimeout(resizeTimer); resizeTimer = window.setTimeout(render, 120); });
  render();
}());
