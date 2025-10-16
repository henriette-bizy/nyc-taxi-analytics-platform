    document.getElementById("button").addEventListener("click", function () {
    const container = document.getElementById("chartbox");
    container.style.display = "grid";
    this.style.display = "none";
    loadCharts();
    });

    function loadCharts() {
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
    }