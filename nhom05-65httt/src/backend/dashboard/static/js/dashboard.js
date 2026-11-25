document.addEventListener("DOMContentLoaded", function () {
    if (typeof Chart === "undefined") return;

    const completionCanvas = document.getElementById("completionChart");
    if (completionCanvas) {
        new Chart(completionCanvas, {
            type: "line",
            data: {
                labels: ["T1", "T2", "T3", "T4", "T5", "T6"],
                datasets: [{
                    label: "Tỷ lệ hoàn thành",
                    data: [78, 81, 80, 83, 84, 86],
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37,99,235,.08)",
                    fill: true,
                    tension: .35,
                    pointRadius: 3
                }]
            },
            options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: false, min: 70, ticks: { callback: value => value + "%" } } } }
        });
    }

    const sectorCanvas = document.getElementById("sectorChart");
    if (sectorCanvas) {
        new Chart(sectorCanvas, {
            type: "doughnut",
            data: {
                labels: ["CNTT", "Kinh tế", "Ngoại ngữ", "Khác"],
                datasets: [{ data: [42, 28, 18, 12], backgroundColor: ["#2563eb", "#60a5fa", "#93c5fd", "#dbeafe"], borderWidth: 0 }]
            },
            options: { responsive: true, cutout: "68%", plugins: { legend: { position: "bottom", labels: { boxWidth: 10, usePointStyle: true } } } }
        });
    }
});
