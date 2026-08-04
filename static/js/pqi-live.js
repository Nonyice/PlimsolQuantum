async function loadPQIState() {

    const response = await fetch("/api/pqi/state");

    if (!response.ok) return;

    const state = await response.json();

    update("pqi-status", state.status);
    update("exchange", state.exchange);
    update("market", state.market);
    update("decision", state.current_decision);
    update("confidence", state.confidence.toFixed(2) + "%");
    update("regime", state.market_regime);
    update("positions", state.open_positions);
    update("portfolio", "$" + state.portfolio_value.toFixed(2));
    update("daily-pnl", "$" + state.daily_pnl.toFixed(2));
    update("task", state.current_task);
    update("signals", state.signals_analysed);
    update("trades", state.trades_today);
    update("winrate", state.win_rate.toFixed(2) + "%");
    update("risk", state.risk_exposure.toFixed(2) + "%");
}

function update(id, value) {

    const el = document.getElementById(id);

    if (el) {

        el.textContent = value;

    }

}

loadPQIState();

setInterval(loadPQIState, 1000);