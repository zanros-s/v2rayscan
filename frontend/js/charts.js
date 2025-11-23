let currentChart = null;
let currentChartServerId = null;
let currentChartServerName = null;


function getSelectedMinutes() {
    const select = document.getElementById("chart-range-select");
    if (!select) {
        return 1440; 
    }
    const value = parseInt(select.value, 10);
    if (isNaN(value) || value <= 0) {
        return 1440;
    }
    return value;
}


function updateChartStats(checks, minutes) {
    const el = document.getElementById("chart-stats");
    if (!el) return;

    if (!Array.isArray(checks) || checks.length === 0) {
        el.textContent = "در این بازه هیچ دیتایی وجود ندارد";
        return;
    }

    const total = checks.length;
    const totalDown = checks.filter(c => c.status === "DOWN").length;

    
    const mins = minutes || getSelectedMinutes();

    el.textContent = `تعداد DOWN در این بازه (${mins} دقیقه اخیر): ${totalDown} از مجموع ${total} چک`;
}

async function showServerChart(serverId, serverName, minutes) {
    try {
        currentChartServerId = serverId;
        currentChartServerName = serverName;

        const mins = minutes || getSelectedMinutes();

        const res = await fetch(`/api/checks/${serverId}?minutes=${mins}`);
        if (!res.ok) {
            alert("خطا در دریافت تاریخچه سرور");
            return;
        }
        const data = await res.json();

        if (!Array.isArray(data) || data.length === 0) {
            alert("هیچ داده‌ای برای این سرور وجود ندارد");
            updateChartStats([], mins);
            return;
        }

 
        const labels = data.map(c => new Date(c.checked_at).toLocaleString());
        const latency = data.map(c => c.latency_ms != null ? c.latency_ms : 0);
        const statusData = data.map(c => c.status === "UP" ? 1 : 0);

        const ctx = document.getElementById("server-chart").getContext("2d");

        if (currentChart) {
            currentChart.destroy();
        }

        currentChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Latency (ms)",
                        data: latency,
                        yAxisID: "y",
                        tension: 0.2,
                        pointRadius: 2
                    },
                    {
                        label: "Status (1=UP, 0=DOWN)",
                        data: statusData,
                        yAxisID: "y1",
                        tension: 0.2,
                        borderDash: [4, 4],
                        pointRadius: 1
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: "index",
                    intersect: false
                },
                scales: {
                    y: {
                        position: "left",
                        title: {
                            display: true,
                            text: "Latency (ms)"
                        }
                    },
                    y1: {
                        position: "right",
                        min: 0,
                        max: 1,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: "Status"
                        }
                    }
                }
            }
        });

        const chartSection = document.getElementById("chart-section");
        const chartTitle = document.getElementById("chart-title");
        chartSection.style.display = "block";
        chartTitle.textContent = `گراف وضعیت سرور: ${serverName}`;

       
        updateChartStats(data, mins);
    } catch (e) {
        console.error(e);
        alert("خطا در رسم گراف");
    }
}


function initChartRangeSelector() {
    const rangeSelect = document.getElementById("chart-range-select");
    if (!rangeSelect) return;

    rangeSelect.addEventListener("change", () => {
        if (!currentChartServerId || !currentChartServerName) {
            return;
        }
        const mins = getSelectedMinutes();
        showServerChart(currentChartServerId, currentChartServerName, mins);
    });
}

document.addEventListener("DOMContentLoaded", initChartRangeSelector);


window.showServerChart = showServerChart;


// ---------- Live Monitor via XRAY ----------



let liveChart = null;
let liveWs = null;


let liveStats = {
    total: 0,
    success: 0,
    down: 0,
    sumLatency: 0,        
    lastLatency: null,
    consecutiveDown: 0,
    lastError: null,
};

function resetLiveStats() {
    liveStats = {
        total: 0,
        success: 0,
        down: 0,
        sumLatency: 0,
        lastLatency: null,
        consecutiveDown: 0,
        lastError: null,
    };
    renderLiveStats();
}

function updateLiveStatsOnSample(ok, latency, error) {
    liveStats.total += 1;

    if (ok) {
        liveStats.success += 1;
        liveStats.lastLatency = latency;
        liveStats.sumLatency += latency || 0;
        liveStats.consecutiveDown = 0;
    } else {
        liveStats.down += 1;
        liveStats.consecutiveDown += 1;
        if (error) {
            liveStats.lastError = error;
        }
    }

    renderLiveStats();
}

function renderLiveStats() {
    const totalEl = document.getElementById("live-total");
    const successEl = document.getElementById("live-success");
    const downEl = document.getElementById("live-down");
    const successRateEl = document.getElementById("live-success-rate");
    const avgLatencyEl = document.getElementById("live-avg-latency");
    const lastLatencyEl = document.getElementById("live-last-latency");
    const consecutiveDownEl = document.getElementById("live-consecutive-down");
    const lastErrorEl = document.getElementById("live-last-error");

    if (!totalEl) return; 

    const { total, success, down, sumLatency, lastLatency, consecutiveDown, lastError } = liveStats;

    const successRate = total > 0 ? Math.round((success / total) * 100) : 0;
    const avgLatency = success > 0 ? Math.round(sumLatency / success) : 0;

    totalEl.textContent = total.toString();
    successEl.textContent = success.toString();
    downEl.textContent = down.toString();
    successRateEl.textContent = successRate.toString() + "%";
    avgLatencyEl.textContent = avgLatency > 0 ? avgLatency + " ms" : "0 ms";
    lastLatencyEl.textContent = lastLatency != null ? Math.round(lastLatency) + " ms" : "-";
    consecutiveDownEl.textContent = consecutiveDown.toString();
    lastErrorEl.textContent = lastError || "-";
}


function setLiveStatus(text, ok = true) {
    const el = document.getElementById("live-status");
    if (!el) return;
    el.textContent = text;
    el.className = "status-text " + (ok ? "success" : "error");
}

function toggleLiveButtons(running) {
    const startBtn = document.getElementById("live-start-btn");
    const stopBtn = document.getElementById("live-stop-btn");
    if (!startBtn || !stopBtn) return;

    startBtn.disabled = running;
    stopBtn.disabled = !running;
}

function initLiveChart() {
    const ctx = document.getElementById("live-chart");
    if (!ctx) return;

    if (liveChart) {
        liveChart.destroy();
    }

    liveChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Latency (ms)",
                    data: [],
                    tension: 0.3,
                    pointRadius: 1.5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "زمان",
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: "ms",
                    },
                    beginAtZero: true,
                },
            },
        },
    });
}

function startLiveMonitor() {
    const linkInput = document.getElementById("live-link");
    const intervalInput = document.getElementById("live-interval");

    if (!linkInput || !intervalInput) return;

    const link = linkInput.value.trim();
    let interval = parseFloat(intervalInput.value) || 0.5;

    if (!link) {
        alert("لطفاً لینک vless/vmess را وارد کنید");
        return;
    }

    if (interval < 0.2) interval = 0.2;

    
    if (liveWs) {
        liveWs.close();
        liveWs = null;
    }

    if (!liveChart) {
        initLiveChart();
    } else {
        liveChart.data.labels = [];
        liveChart.data.datasets[0].data = [];
        liveChart.update();
    }

    // stats reset
    resetLiveStats();

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/api/monitor/ws`;

    liveWs = new WebSocket(wsUrl);

    liveWs.onopen = (event) => {
        toggleLiveButtons(true);
        setLiveStatus("در حال رصد از طریق XRAY...", true);

        const socket = event.target;
        try {
            socket.send(
                JSON.stringify({
                    link: link,
                    interval: interval,
                })
            );
        } catch (e) {
            console.error("خطا در ارسال پیام اولیه WebSocket", e);
            setLiveStatus("خطا در شروع رصد", false);
        }
    };



    liveWs.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);

            if (msg.type === "sample") {
                const label = new Date(msg.ts).toLocaleTimeString();

                liveChart.data.labels.push(label);
                liveChart.data.datasets[0].data.push(
                    msg.ok ? msg.latency_ms : null
                );

                const maxPoints = 1000; 
                if (liveChart.data.labels.length > maxPoints) {
                    liveChart.data.labels.shift();
                    liveChart.data.datasets[0].data.shift();
                }

                liveChart.update("none");

                
                updateLiveStatsOnSample(msg.ok, msg.latency_ms, msg.error);

                if (!msg.ok) {
                    setLiveStatus(
                        msg.error || "خطا در اتصال از طریق XRAY",
                        false
                    );
                } else {
                    setLiveStatus("در حال رصد از طریق XRAY...", true);
                }
            } else if (msg.type === "error") {
                setLiveStatus(msg.message || "خطای مانیتور", false);
            }
        } catch (e) {
            console.error("live monitor parse error", e);
        }
    };

    liveWs.onclose = () => {
        toggleLiveButtons(false);
        setLiveStatus("مانیتور متوقف شد", false);
        liveWs = null;
    };

    liveWs.onerror = () => {
        setLiveStatus("خطا در ارتباط WebSocket", false);
    };
}

function stopLiveMonitor() {
    if (liveWs) {
        liveWs.close();
        liveWs = null;
    }
}

window.startLiveMonitor = startLiveMonitor;
window.stopLiveMonitor = stopLiveMonitor;
window.addEventListener("beforeunload", () => {
    if (liveWs) {
        try {
            liveWs.close();
        } catch (e) {
            console.warn("خطا در بستن WebSocket هنگام unload", e);
        }
    }
});
