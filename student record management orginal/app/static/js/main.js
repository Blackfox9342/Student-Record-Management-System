document.addEventListener("DOMContentLoaded", () => {
  const trendCanvas = document.getElementById("adminTrendChart");
  if (!trendCanvas || !window.PRAKASH_CHART || !window.PRAKASH_CHART.adminTrend) {
    return;
  }

  const chartData = window.PRAKASH_CHART.adminTrend;
  new Chart(trendCanvas, {
    type: "line",
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: "Students",
          data: chartData.data,
          borderColor: "#5eead4",
          backgroundColor: "rgba(94, 234, 212, 0.2)",
          tension: 0.35,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: "#5eead4",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#eef4ff",
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "rgba(238, 244, 255, 0.72)" },
          grid: { color: "rgba(255, 255, 255, 0.06)" },
        },
        y: {
          ticks: { color: "rgba(238, 244, 255, 0.72)" },
          grid: { color: "rgba(255, 255, 255, 0.06)" },
        },
      },
    },
  });
});
