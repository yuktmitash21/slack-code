(() => {
  const HOUR_MS = 60 * 60 * 1000;
  const DAY_MS = 24 * HOUR_MS;
  const DEFAULT_RANGE = "3d";

  let rawData = [];
  let lineChart = null;
  let barChart = null;
  let processingTimeChart = null;

  const elements = {
    dateRange: document.getElementById("date-range"),
    mergeRate: document.getElementById("merge-rate-value"),
    totalPrs: document.getElementById("total-prs"),
    mergedPrs: document.getElementById("merged-prs"),
    avgPrs: document.getElementById("avg-prs"),
    avgPrsLabel: document.getElementById("avg-prs-label"),
    avgProcessingTime: document.getElementById("avg-processing-time"),
    lineEmpty: document.getElementById("line-empty-state"),
    barEmpty: document.getElementById("bar-empty-state"),
    processingEmpty: document.getElementById("processing-empty-state"),
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
    renderProcessingTimeChart(filtered);
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
      case "3d":
      default: {
        const end = new Date(now);
        end.setHours(23, 59, 59, 999);
        const start = new Date(end);
        start.setDate(start.getDate() - 2);
        start.setHours(0, 0, 0, 0);
        return { mode: "day", start, end, days: 3 };
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
    let timeUnit;
    if (meta.mode === "day") {
      windowUnits = meta.days || Math.max(1, Math.round((meta.end - meta.start) / DAY_MS));
      timeUnit = windowUnits === 1 ? "day" : "day";
    } else {
      windowUnits = meta.hours || Math.max(1, Math.round((meta.end - meta.start) / HOUR_MS));
      timeUnit = windowUnits === 1 ? "hour" : "hour";
    }

    // Update the label to show the actual time unit
    elements.avgPrsLabel.textContent = `Avg PRs / ${timeUnit}`;

    const avgPerPeriod = total === 0 ? 0 : total / windowUnits;
    elements.avgPrs.textContent = avgPerPeriod.toFixed(1);

    // Calculate average processing time
    const prsWithTime = filtered.filter((item) => item.processing_time_ms != null);
    if (prsWithTime.length > 0) {
      const totalTimeMs = prsWithTime.reduce((sum, item) => sum + item.processing_time_ms, 0);
      const avgTimeMs = totalTimeMs / prsWithTime.length;
      const avgTimeSeconds = avgTimeMs / 1000;
      
      if (avgTimeSeconds < 1) {
        elements.avgProcessingTime.textContent = `${avgTimeMs.toFixed(0)}ms`;
      } else if (avgTimeSeconds < 60) {
        elements.avgProcessingTime.textContent = `${avgTimeSeconds.toFixed(1)}s`;
      } else {
        const minutes = Math.floor(avgTimeSeconds / 60);
        const seconds = Math.floor(avgTimeSeconds % 60);
        elements.avgProcessingTime.textContent = `${minutes}m ${seconds}s`;
      }
    } else {
      elements.avgProcessingTime.textContent = "--";
    }
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

    const allChannels = Object.entries(channelCounts)
      .sort((a, b) => b[1] - a[1]);

    const topChannels = allChannels.slice(0, 7);
    const others = allChannels.slice(7);

    if (!topChannels.length) {
      elements.barEmpty.classList.remove("hidden");
      return;
    }

    elements.barEmpty.classList.add("hidden");

    // Prepare data for pie chart
    const labels = topChannels.map(([name]) => name);
    const data = topChannels.map(([_, count]) => count);

    // Add "Others" slice if there are more than 7 channels
    if (others.length > 0) {
      const othersCount = others.reduce((sum, [_, count]) => sum + count, 0);
      labels.push("Others");
      data.push(othersCount);
    }

    // Calculate total from actual pie chart data (sum of all values)
    // This ensures percentages are calculated correctly based on what's shown in the chart
    const total = data.reduce((sum, count) => sum + count, 0);

    // Generate colors for pie chart
    const colors = [
      "rgba(56, 189, 248, 0.8)",   // cyan
      "rgba(129, 140, 248, 0.8)",   // indigo
      "rgba(167, 139, 250, 0.8)",   // purple
      "rgba(236, 72, 153, 0.8)",    // pink
      "rgba(251, 146, 60, 0.8)",    // orange
      "rgba(34, 197, 94, 0.8)",     // green
      "rgba(59, 130, 246, 0.8)",    // blue
      "rgba(148, 163, 184, 0.8)",   // gray for Others
    ];

    barChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [
          {
            data: data,
            backgroundColor: colors.slice(0, labels.length),
            borderColor: "rgba(11, 18, 33, 0.8)",
            borderWidth: 2,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
          legend: {
            display: true,
            position: "right",
            labels: {
              color: "#94a3b8",
              padding: 12,
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || "";
                const value = context.parsed || 0;
                // Calculate total from the dataset data to ensure accurate percentages
                const datasetTotal = context.dataset.data.reduce((sum, val) => sum + val, 0);
                const percentage = datasetTotal > 0 ? ((value / datasetTotal) * 100).toFixed(1) : 0;
                return `${label}: ${value} PR${value !== 1 ? "s" : ""} (${percentage}%)`;
              },
            },
            backgroundColor: "rgba(16, 27, 51, 0.95)",
            titleColor: "#e2e8f0",
            bodyColor: "#94a3b8",
            borderColor: "rgba(148, 163, 184, 0.2)",
            borderWidth: 1,
            padding: 12,
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

  function renderProcessingTimeChart(filtered) {
    const ctx = document.getElementById("processing-time-chart");
    if (!ctx) return;

    if (processingTimeChart) {
      processingTimeChart.destroy();
      processingTimeChart = null;
    }

    // Filter data with processing time
    const dataWithTime = filtered.filter((item) => item.processing_time_ms != null);

    if (!dataWithTime.length) {
      elements.processingEmpty.classList.remove("hidden");
      return;
    }

    elements.processingEmpty.classList.add("hidden");

    // Define time segments (in milliseconds)
    const segments = [
      { label: "< 1s", max: 1000 },
      { label: "1-5s", min: 1000, max: 5000 },
      { label: "5-10s", min: 5000, max: 10000 },
      { label: "10-30s", min: 10000, max: 30000 },
      { label: "30-60s", min: 30000, max: 60000 },
      { label: "> 60s", min: 60000 },
    ];

    // Count PRs in each segment
    const segmentCounts = segments.map((segment) => {
      const count = dataWithTime.filter((item) => {
        const time = item.processing_time_ms;
        if (segment.min !== undefined && segment.max !== undefined) {
          return time >= segment.min && time < segment.max;
        } else if (segment.max !== undefined) {
          return time < segment.max;
        } else {
          return time >= segment.min;
        }
      }).length;
      return { label: segment.label, count };
    });

    const labels = segmentCounts.map((s) => s.label);
    const counts = segmentCounts.map((s) => s.count);

    processingTimeChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "PR Count",
            data: counts,
            backgroundColor: "rgba(56, 189, 248, 0.8)",
            borderRadius: 6,
          },
        ],
      },
      options: {
        indexAxis: "y", // Horizontal bar chart
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const count = context.parsed.x;
                const total = dataWithTime.length;
                const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                return `${count} PR${count !== 1 ? "s" : ""} (${percentage}%)`;
              },
            },
            backgroundColor: "rgba(16, 27, 51, 0.95)",
            titleColor: "#e2e8f0",
            bodyColor: "#94a3b8",
            borderColor: "rgba(148, 163, 184, 0.2)",
            borderWidth: 1,
            padding: 12,
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              color: "#94a3b8",
              precision: 0,
            },
            grid: {
              color: "rgba(148, 163, 184, 0.15)",
            },
          },
          y: {
            ticks: {
              color: "#94a3b8",
            },
            grid: {
              display: false,
            },
          },
        },
      },
    });
  }
})();

