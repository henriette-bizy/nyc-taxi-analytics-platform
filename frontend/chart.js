    document.getElementById("button").addEventListener("click", function () {
    const container = document.getElementById("chartbox");
    container.style.display = "grid";
    this.style.display = "none";
    loadCharts();
    });

    function loadCharts() {
    // chart for bar
    new Chart(document.getElementById("barchart"), {
        type: "bar",
        data: {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
        datasets: [
            {
            label: "Sales ($)",
            data: [1200, 1500, 1000, 1800, 2200],
            backgroundColor: "#ff5b2e",
            borderRadius: 8,
            },
        ],
        },
        options: {
        responsive: true,
        scales: { y: { beginAtZero: true } },
        },
    });

    // chart for line
    new Chart(document.getElementById("linechart"), {
        type: "line",
        data: {
        labels: ["1", "2", "3", "4"],
        datasets: [
            {
            label: "Trend in trips",
            data: [65, 59, 80, 81, 56],
            borderColor: "#1e90ff",
            fill: false,
            tension: 0.3,
            },
        ],
        },
        options: { responsive: true },
    });

    // chart for pie
    new Chart(document.getElementById("piechart"), {
        type: "pie",
        data: {
        labels: ["New York", "Bronx", "Brooklyn", "Other"],
        datasets: [
            {
            data: [45, 25, 20, 10],
            backgroundColor: ["#ff5b2e", "#1e90ff", "#ffb400", "#4caf50"],
            },
        ],
        },
        options: { responsive: true },
    });

    // chart for doughnut
    new Chart(document.getElementById("doughnutchart"), {
        type: "doughnut",
        data: {
        labels: ["-40km/h", "60km/h", "80km/h+"],
        datasets: [
            {
            data: [70, 20, 10],
            backgroundColor: ["#4caf50", "#ffb400", "#ff5b2e"],
            },
        ],
        },
        options: {
        responsive: true,
        cutout: "70%",
        plugins: {
            legend: { position: "bottom" },
        },
    },
    });
    }