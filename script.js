const canvas = document.getElementById("energyChart");

if (canvas && typeof Chart !== "undefined") {
    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const values = JSON.parse(canvas.dataset.values || "[]");

    const chartColors = [
        "#2dd4bf",
        "#60a5fa",
        "#fbbf24",
        "#c084fc",
        "#fb7185",
        "#a3e635",
        "#38bdf8"
    ];

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Energy consumption (kWh)",
                data: values,
                backgroundColor: labels.map(
                    (_, i) => chartColors[i % chartColors.length]
                ),
                borderRadius: 7,
                maxBarThickness: 65
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: "#e2e8f0"
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: "#cbd5e1"
                    },
                    grid: {
                        color: "#334155"
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Energy (kWh)",
                        color: "#cbd5e1"
                    },
                    ticks: {
                        color: "#cbd5e1"
                    },
                    grid: {
                        color: "#334155"
                    }
                }
            }
        }
    });
}