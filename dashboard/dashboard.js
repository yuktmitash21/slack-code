(() => {
  const HOUR_MS = 60 * 60 * 1000;
  const DAY_MS = 24 * HOUR_MS;
  const DEFAULT_RANGE = "7d";

  let rawData = [];
  let lineChart = null;
  let barChart = null;

  const elements = {
    dateRange: document.getElementById("date-range"),
    mergeRate: document.getElementById("merge-rate-value"),
    totalPrs: document.getElementById("total-prs"),
    mergedPrs: document.getElementById("merged-prs"),
    avgPrs: document.getElementById("avg-prs"),
    lineEmpty: document.getElementById("line-empty-state"),
    barEmpty: document.getElementById("bar-empty-state"),
    errorBanner: document.getElementById("error-banner"),
  };

  document.addEventListener("DOMContentLoaded", async () => {
    await loadData();
    if (!elements.dateRange.value) {
      elements.dateRange.value = DEFAULT_RANGE;
    }
    setupListeners();
    render();
  });

  async function loadData() {
    try {
      const response = await fetch("../data/pr_activity.json", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Failed to load analytics file (${response.status})`);
      }
      rawData = await response.json();
      elements.errorBanner.style.display = "none";
    } catch (error) {
      elements.errorBanner.textContent = `Unable to load analytics data: ${error.message}`;
      elements.errorBanner.style.display = "block";
      rawData = [];
    }
  }

  function setupListeners() {
    elements.dateRange.addEventListener("change", render);
  }

  function render() {
    const rangeKey = elements.dateRange.value || DEFAULT_RANGE;
    const meta = resolveRangeMeta(rangeKey);
    const filtered = filterByRange(rawData, meta);

    updateSummary(filtered, meta);
    renderLineChart(filtered, meta);
    renderBarChart(filtered);
  }

  function resolveRangeMeta(rangeKey) {
    const now = new Date();
    switch (rangeKey) {
      case "1h": {
        const start = new Date(now.getTime() - HOUR_MS);
        return { mode: "hour", start, end: now, bucketMinutes: 5, hours: 1 };
      }
      case "6h": {
        const start = new Date(now.getTime() - 6 * HOUR_MS);
        return { mode: "hour", start, end: now, bucketMinutes: 30, hours: 6 };
      }
      case "today": {
        const start = new Date(now);
        start.setHours(0, 0, 0, 0);
        const hours = Math.max(1, Math.ceil((now - start) / HOUR_MS));
        return { mode: "hour", start, end: now, bucketMinutes: 60, hours };
      }
      case "7d":
      default: {
        const end = new Date(now);
        end.setHours(23, 59, 59, 999);
        const start = new Date(end);
        start.setDate(start.getDate() - 6);
        start.setHours(0, 0, 0, 0);
        return { mode: "day", start, end, days: 7 };
      }
    }
  }

  function filterByRange(data, meta) {
    if (!data || !data.length) return [];
    return data.filter((record) => {
      if (!record.created_at) return false;
      const created = new Date(record.created_at);
      return !Number.isNaN(created) && created >= meta.start && created <= meta.end;
    });
  }

  function updateSummary(filtered, meta) {
    const total = filtered.length;
    const merged = filtered.filter((item) => item.merged).length;
    const mergeRate = total === 0 ? 0 : (merged / total) * 100;

    elements.totalPrs.textContent = total;
    elements.mergedPrs.textContent = merged;
    elements.mergeRate.textContent = `${mergeRate.toFixed(1)}%`;

    let windowUnits;
    if (meta.mode === "day") {
      windowUnits = meta.days || Math.max(1, Math.round((meta.end - meta.start) / DAY_MS));
    } else {
      windowUnits = meta.hours || Math.max(1, Math.round((meta.end - meta.start) / HOUR_MS));
    }

    const avgPerPeriod = total === 0 ? 0 : total / windowUnits;
    elements.avgPrs.textContent = avgPerPeriod.toFixed(1);
  }

  function renderLineChart(filtered, meta) {
    const ctx = document.getElementById("pr-over-time-chart");
    if (!ctx) return;

    if (lineChart) {
      lineChart.destroy();
      lineChart = null;
    }

    if (!filtered.length) {
      elements.lineEmpty.classList.remove("hidden");
      return;
    }

    elements.lineEmpty.classList.add("hidden");

    const series = buildTimeSeries(filtered, meta);
    lineChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: series.labels,
        datasets: [
          {
            label: "PRs created",
            data: series.values,
            borderColor: "rgba(56, 189, 248, 1)",
            backgroundColor: "rgba(56, 189, 248, 0.15)",
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 3,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            ticks: { color: "#94a3b8" },
            grid: { color: "rgba(148, 163, 184, 0.15)" },
          },
          y: {
            beginAtZero: true,
            ticks: { color: "#94a3b8", precision: 0 },
            grid: { color: "rgba(148, 163, 184, 0.15)" },
          },
        },
      },
    });
  }

  function renderBarChart(filtered) {
    const ctx = document.getElementById("top-channels-chart");
    if (!ctx) return;

    if (barChart) {
      barChart.destroy();
      barChart = null;
    }

    if (!filtered.length) {
      elements.barEmpty.classList.remove("hidden");
      return;
    }

    const channelCounts = filtered.reduce((acc, item) => {
      const label = item.channel_name || item.channel_id || "Unknown";
      acc[label] = (acc[label] || 0) + 1;
      return acc;
    }, {});

    const topChannels = Object.entries(channelCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    if (!topChannels.length) {
      elements.barEmpty.classList.remove("hidden");
      return;
    }

    elements.barEmpty.classList.add("hidden");

    barChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: topChannels.map(([name]) => name),
        datasets: [
          {
            label: "PR count",
            data: topChannels.map(([_, count]) => count),
            backgroundColor: "rgba(129, 140, 248, 0.7)",
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            ticks: { color: "#94a3b8" },
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            ticks: { color: "#94a3b8", precision: 0 },
            grid: { color: "rgba(148, 163, 184, 0.15)" },
          },
        },
      },
    });
  }

  function buildTimeSeries(filtered, meta) {
    if (meta.mode === "day") {
      return buildDailySeries(filtered, meta);
    }
    return buildHourlySeries(filtered, meta);
  }

  function buildHourlySeries(filtered, meta) {
    const start = new Date(meta.start);
    const end = new Date(meta.end);
    const bucketMinutes = meta.bucketMinutes || 60;
    const bucketMs = bucketMinutes * 60 * 1000;
    const totalMs = Math.max(bucketMs, end - start);
    const bucketCount = Math.ceil(totalMs / bucketMs);

    const labels = [];
    const values = new Array(bucketCount).fill(0);

    for (let i = 0; i < bucketCount; i++) {
      const tick = new Date(start.getTime() + i * bucketMs);
      labels.push(
        tick.toLocaleTimeString([], {
          hour: "numeric",
          minute: bucketMinutes >= 60 ? undefined : "2-digit",
        })
      );
    }

    filtered.forEach((item) => {
      const created = new Date(item.created_at);
      if (created < start || created > end) return;
      const diff = created - start;
      const idx = Math.min(values.length - 1, Math.floor(diff / bucketMs));
      if (idx >= 0) {
        values[idx] += 1;
      }
    });

    return { labels, values };
  }

  function buildDailySeries(filtered, meta) {
    const dayCount = meta.days || Math.max(1, Math.round((meta.end - meta.start) / DAY_MS));
    const labels = [];
    const values = new Array(dayCount).fill(0);

    for (let i = 0; i < dayCount; i++) {
      const day = new Date(meta.start.getTime());
      day.setDate(meta.start.getDate() + i);
      labels.push(day.toLocaleDateString(undefined, { month: "short", day: "numeric" }));
    }

    filtered.forEach((item) => {
      const created = new Date(item.created_at);
      const dayStart = new Date(created);
      dayStart.setHours(0, 0, 0, 0);
      const diff = Math.floor((dayStart - meta.start) / DAY_MS);
      if (diff >= 0 && diff < values.length) {
        values[diff] += 1;
      }
    });

    return { labels, values };
  }
})();

