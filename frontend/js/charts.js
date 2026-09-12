/**
 * Amahirwe: small dependency-free chart helpers (donut ring, bar rows,
 * mini bar-over-time chart). Every value passed in must be a real
 * computed number from the API, never a placeholder, per the
 * project-wide rule against fabricated statistics.
 */

/** A single labelled progress bar row, e.g. one talent area's score. */
function barRow(label, icon, value, max) {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0;
  return `
    <div class="chart-bar-row">
      <span class="chart-bar-row__label">${icon || ""} ${label}</span>
      <span class="chart-bar-row__track"><span class="chart-bar-row__fill" style="width:${percent}%"></span></span>
      <span class="chart-bar-row__value">${value}</span>
    </div>`;
}

/** A circular progress ring with a percentage in the middle. */
function donutRing(percent, { size = 96, stroke = 10, color = "var(--color-primary-teal)" } = {}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(Math.max(percent, 0), 100) / 100);
  const center = size / 2;
  return `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="${percent}%">
      <circle cx="${center}" cy="${center}" r="${radius}" fill="none" stroke="var(--color-bg-secondary)" stroke-width="${stroke}" />
      <circle cx="${center}" cy="${center}" r="${radius}" fill="none" stroke="${color}" stroke-width="${stroke}"
        stroke-linecap="round" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
        transform="rotate(-90 ${center} ${center})" />
      <text x="${center}" y="${center}" text-anchor="middle" dominant-baseline="central" class="chart-donut__value">${percent}%</text>
    </svg>`;
}

/** A row of vertical bars for a time series, e.g. signups per day. Each
 * point is {date: "YYYY-MM-DD", count: number}. */
function miniBarChart(points) {
  const max = Math.max(1, ...points.map((p) => p.count));
  return `
    <div class="mini-bars">
      ${points
        .map((p) => {
          const height = Math.max(2, Math.round((p.count / max) * 100));
          const day = new Date(p.date + "T00:00:00").toLocaleDateString(undefined, { day: "numeric" });
          return `<div class="mini-bars__col" title="${p.date}: ${p.count}">
            <span class="mini-bars__bar" style="height:${height}%"></span>
            <span class="mini-bars__col-label">${day}</span>
          </div>`;
        })
        .join("")}
    </div>`;
}

export { barRow, donutRing, miniBarChart };
