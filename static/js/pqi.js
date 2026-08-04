async function loadPQIState() {

    const response = await fetch("/api/pqi/state");

    const state = await response.json();

    document.getElementById("exchange").textContent = state.exchange || "--";
    document.getElementById("market").textContent = state.market || "--";
    document.getElementById("decision").textContent = state.current_decision;
    document.getElementById("confidence").textContent = state.confidence.toFixed(2) + "%";
    document.getElementById("regime").textContent = state.market_regime || "--";
    document.getElementById("positions").textContent = state.open_positions;
    document.getElementById("portfolio").textContent = "$" + state.portfolio_value.toFixed(2);
    document.getElementById("daily-pnl").textContent = "$" + state.daily_pnl.toFixed(2);
    document.getElementById("task").textContent = state.current_task;
    document.getElementById("signals").textContent = state.signals_analysed;
    document.getElementById("trades").textContent = state.trades_today;
    document.getElementById("winrate").textContent = state.win_rate.toFixed(2) + "%";
    document.getElementById("risk").textContent = state.risk_exposure.toFixed(2) + "%";

    const status = document.querySelector(".success");

    if (status) {

        status.textContent = "● " + state.status;

    }

}

async function engagePQI() {

    await fetch("/api/pqi/engage", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            exchange: "Binance",

            market: "BTCUSDT"

        })

    });

}

async function pausePQI() {

    await fetch("/api/pqi/pause", {

        method: "POST"

    });

}

async function stopPQI() {

    await fetch("/api/pqi/stop", {

        method: "POST"

    });

}

document
    .getElementById("engage-pqi")
    ?.addEventListener("click", engagePQI);

document
    .getElementById("pause-pqi")
    ?.addEventListener("click", pausePQI);

document
    .getElementById("stop-pqi")
    ?.addEventListener("click", stopPQI);

loadPQIState();

setInterval(loadPQIState, 1000);