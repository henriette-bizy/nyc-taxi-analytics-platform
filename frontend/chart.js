async function fetchJSON(url) {
  const res = await fetch(url);
  return res.json();
}

async function loadCharts() {
  const hourly = await fetchJSON(
    `${window.API_BASE}/api/trips/analytics/hourly`
  );
  const labels = hourly.map((d) => Number(d.pickup_hour));
  const counts = hourly.map((d) => Number(d.trip_count) || 0);
  new Chart(document.getElementById("linechart"), {
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

  const peak = counts.reduce(
    (a, b, i) => (labels[i] >= 7 && labels[i] <= 20 ? a + b : a),
    0
  );
  const offpeak = counts.reduce(
    (a, b, i) => (labels[i] < 7 || labels[i] > 20 ? a + b : a),
    0
  );
  new Chart(document.getElementById("donutchart"), {
    type: "doughnut",
    data: {
      labels: ["Peak (7-20)", "Off-Peak"],
      datasets: [
        { data: [peak, offpeak], backgroundColor: ["#7c5cff", "#1f2937"] },
      ],
    },
    options: { responsive: true },
  });

  const vendors = await fetchJSON(`${window.API_BASE}/api/vendors`);
  document.getElementById("kpi-peak").textContent = peak.toLocaleString();
  document.getElementById("kpi-offpeak").textContent = offpeak.toLocaleString();
  document.getElementById("kpi-vendors").textContent = vendors.length;

  const tbody = document.getElementById("vendor-rows");
  tbody.innerHTML = vendors
    .map(
      (v) =>
        `<tr><td>${v.vendor_id}</td><td>${v.vendor_name}</td><td>${
          v.description || ""
        }</td></tr>`
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

document.addEventListener("DOMContentLoaded", loadCharts);
