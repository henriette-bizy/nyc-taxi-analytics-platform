async function fetchJSON(url) {
  const res = await fetch(url);
  return res.json();
}

let lineChart, donutChart;
let cachedData = { hourly: [], vendors: [] };

async function loadCharts() {
  cachedData.hourly = await fetchJSON(`${window.API_BASE}/api/trips/analytics/hourly`);
  cachedData.vendors = await fetchJSON(`${window.API_BASE}/api/vendors`);

  renderCharts(cachedData.hourly);
  renderVendors(cachedData.vendors);
  setupFilters();
}

function renderCharts(hourly) {
  const labels = hourly.map((d) => Number(d.pickup_hour));
  const counts = hourly.map((d) => Number(d.trip_count) || 0);

  if (lineChart) lineChart.destroy();
  if (donutChart) donutChart.destroy();

  lineChart = new Chart(document.getElementById("linechart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Trips per hour",
          data: counts,
          borderColor: "#5b8def",
          backgroundColor: "rgba(91,141,239,0.2)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: { responsive: true },
  });

  const peak = counts.reduce((a, b, i) => (labels[i] >= 7 && labels[i] <= 20 ? a + b : a), 0);
  const offpeak = counts.reduce((a, b, i) => (labels[i] < 7 || labels[i] > 20 ? a + b : a), 0);

  donutChart = new Chart(document.getElementById("donutchart"), {
    type: "doughnut",
    data: {
      labels: ["Peak (7–20)", "Off-Peak"],
      datasets: [
        { data: [peak, offpeak], backgroundColor: ["#7c5cff", "#1f2937"] },
      ],
    },
    options: { responsive: true },
  });

  // Update KPI values
  document.getElementById("kpi-peak").textContent = peak.toLocaleString();
  document.getElementById("kpi-offpeak").textContent = offpeak.toLocaleString();
  document.getElementById("kpi-vendors").textContent = cachedData.vendors.length;
}

function renderVendors(vendors) {
  const tbody = document.getElementById("vendor-rows");
  tbody.innerHTML = vendors
    .map(
      (v) =>
        `<tr>
          <td>${v.vendor_id}</td>
          <td>${v.vendor_name}</td>
          <td>${v.description || ""}</td>
        </tr>`
    )
    .join("");

  const search = document.getElementById("vendor-search");
  search.addEventListener("input", () => {
    const q = search.value.toLowerCase();
    Array.from(tbody.querySelectorAll("tr")).forEach((tr) => {
      const txt = tr.textContent.toLowerCase();
      tr.style.display = txt.includes(q) ? "" : "none";
    });
  });
}

function setupFilters() {
  const hourFilter = document.getElementById("hour-filter");
  const vendorSort = document.getElementById("vendor-sort");

  hourFilter.addEventListener("change", (e) => {
    const val = e.target.value;
    let filtered = [...cachedData.hourly];

    switch (val) {
      case "morning":
        filtered = filtered.filter((d) => d.pickup_hour >= 5 && d.pickup_hour <= 11);
        break;
      case "afternoon":
        filtered = filtered.filter((d) => d.pickup_hour >= 12 && d.pickup_hour <= 17);
        break;
      case "evening":
        filtered = filtered.filter((d) => d.pickup_hour >= 18 && d.pickup_hour <= 23);
        break;
      case "night":
        filtered = filtered.filter((d) => d.pickup_hour >= 0 && d.pickup_hour <= 4);
        break;
      default:
        break;
    }
    renderCharts(filtered);
  });

  vendorSort.addEventListener("change", (e) => {
    const val = e.target.value;
    let sorted = [...cachedData.vendors];
    if (val === "name") sorted.sort((a, b) => a.vendor_name.localeCompare(b.vendor_name));
    else sorted.sort((a, b) => a.vendor_id - b.vendor_id);
    renderVendors(sorted);
  });
}

document.addEventListener("DOMContentLoaded", loadCharts);
