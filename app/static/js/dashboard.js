/**
 * Dashboard Analytics and Dynamic Chart.js Rendering
 */

document.addEventListener("DOMContentLoaded", () => {
  loadDashboardAnalytics();
});

let docTypeChartInstance = null;
let activityChartInstance = null;

async function loadDashboardAnalytics() {
  try {
    const response = await fetch("/api/dashboard/stats");
    if (!response.ok) return;

    const stats = await response.json();

    // 1. Render Document Distribution Doughnut Chart
    const docTypeCanvas = document.getElementById("docTypeChart");
    if (docTypeCanvas) {
      const labels = stats.type_distribution.labels;
      const data = stats.type_distribution.data;
      const totalDocs = data.reduce((a, b) => a + b, 0);

      const ctx = docTypeCanvas.getContext("2d");
      if (docTypeChartInstance) docTypeChartInstance.destroy();

      if (totalDocs === 0) {
        // Empty state
        docTypeChartInstance = new Chart(ctx, {
          type: "doughnut",
          data: {
            labels: ["No Documents"],
            datasets: [{ data: [1], backgroundColor: ["#e2e8f0"] }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            cutout: "75%"
          }
        });
      } else {
        docTypeChartInstance = new Chart(ctx, {
          type: "doughnut",
          data: {
            labels: labels,
            datasets: [{
              data: data,
              backgroundColor: ["#f87171", "#60a5fa", "#94a3b8"],
              borderColor: "#ffffff",
              borderWidth: 2,
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: { boxWidth: 12, padding: 15, font: { family: "Inter", size: 12 } }
              }
            },
            cutout: "70%"
          }
        });
      }
    }

    // 2. Render Search Activity 7-day Line Chart
    const activityCanvas = document.getElementById("searchActivityChart");
    if (activityCanvas) {
      const ctx = activityCanvas.getContext("2d");
      if (activityChartInstance) activityChartInstance.destroy();

      const gradient = ctx.createLinearGradient(0, 0, 0, 240);
      gradient.addColorStop(0, "rgba(79, 70, 229, 0.25)");
      gradient.addColorStop(1, "rgba(79, 70, 229, 0.0)");

      activityChartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels: stats.search_activity.labels,
          datasets: [{
            label: "Search Queries",
            data: stats.search_activity.data,
            borderColor: "#4f46e5",
            backgroundColor: gradient,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: "#ffffff",
            pointBorderColor: "#4f46e5",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "#0f172a",
              titleFont: { family: "Inter", size: 12, weight: "bold" },
              bodyFont: { family: "Inter", size: 12 },
              padding: 10,
              displayColors: false
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { font: { family: "Inter", size: 11 }, color: "#94a3b8" }
            },
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1, font: { family: "Inter", size: 11 }, color: "#94a3b8" },
              grid: { color: "#f1f5f9" }
            }
          }
        }
      });
    }
  } catch (err) {
    console.error("Error loading analytics:", err);
  }
}
