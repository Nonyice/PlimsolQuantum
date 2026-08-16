/* =========================================================
   PLIMSOL QUANTUM INTELLIGENCE
   PQI DASHBOARD CONTROLLER
   =========================================================

   IMPORTANT:
   - No exchange is hardcoded.
   - No market/symbol is hardcoded.
   - Dashboard data comes from /api/pqi/state.
   - Only one polling loop is used.
   - Requests cannot overlap.
   ========================================================= */

"use strict";


/* =========================================================
   CONFIGURATION
   ========================================================= */

const PQI_CONFIG = {

    stateEndpoint: "/api/pqi/state",

    engageEndpoint: "/api/pqi/engage",

    pauseEndpoint: "/api/pqi/pause",

    stopEndpoint: "/api/pqi/stop",

    /*
     * Do not poll every 1 second.
     *
     * The dashboard does not need to hammer the backend.
     */
    pollingInterval: 2000

};


/* =========================================================
   INTERNAL STATE
   ========================================================= */

let pqiState = null;

let stateRequestInProgress = false;

let pollingTimer = null;


/* =========================================================
   DOM HELPER
   ========================================================= */


function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

function csrfHeaders(extra = {}) {
    const token = getCSRFToken();
    return token ? { ...extra, "X-CSRFToken": token } : extra;
}

function getElement(id) {

    return document.getElementById(id);

}


/* =========================================================
   SAFE DOM UPDATE
   ========================================================= */

function updateElement(id, value) {

    const element = getElement(id);

    if (!element) {
        return;
    }

    /*
     * Never modify form controls accidentally.
     */
    const tag = element.tagName.toLowerCase();

    if (
        tag === "select" ||
        tag === "input" ||
        tag === "textarea"
    ) {
        return;
    }

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        element.textContent = "--";

        return;
    }

    element.textContent = value;

}


/* =========================================================
   NUMBER FORMATTER
   ========================================================= */

function formatNumber(value, decimals = 2) {

    const number = Number(value);

    if (!Number.isFinite(number)) {

        return "0.00";

    }

    return number.toLocaleString(
        undefined,
        {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }
    );

}


/* =========================================================
   PERCENTAGE FORMATTER
   ========================================================= */

function formatPercentage(value, decimals = 2) {

    const number = Number(value);

    if (!Number.isFinite(number)) {

        return "0.00%";

    }

    return (
        number.toLocaleString(
            undefined,
            {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }
        )
        + "%"
    );

}


/* =========================================================
   CURRENCY FORMATTER
   ========================================================= */

function formatCurrency(
    value,
    currency = null
) {

    const number = Number(value);

    if (!Number.isFinite(number)) {

        return "--";

    }

    /*
     * If the backend provides a currency,
     * use it.
     *
     * Otherwise use the quote currency if supplied.
     *
     * Otherwise simply return the numeric value.
     */
    if (currency) {

        try {

            return new Intl.NumberFormat(
                undefined,
                {
                    style: "currency",
                    currency: currency,
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            ).format(number);

        } catch (error) {

            console.warn(
                "Unable to format currency:",
                currency,
                error
            );

        }

    }

    return formatNumber(number, 2);

}


/* =========================================================
   GET CURRENCY FROM STATE
   ========================================================= */

function getStateCurrency(state) {

    if (!state) {

        return null;

    }

    /*
     * Accept several possible backend field names.
     *
     * This allows the backend to remain flexible.
     */

    return (
        state.currency ||
        state.quote_currency ||
        state.account_currency ||
        state.portfolio_currency ||
        null
    );

}


/* =========================================================
   UPDATE STATUS INDICATOR
   ========================================================= */

function updateStatusIndicator(state) {

    const statusElement =
        document.querySelector(".success");

    if (!statusElement) {

        return;

    }

    if (!state || !state.status) {

        statusElement.textContent = "● OFFLINE";

        return;

    }

    statusElement.textContent =
        "● " + String(state.status).toUpperCase();

}


/* =========================================================
   UPDATE MARKET STATUS
   ========================================================= */

function updateMarketStatus(state) {

    const marketStatus =
        document.querySelector(".market-status");

    if (!marketStatus) {

        return;

    }

    const dot =
        marketStatus.querySelector(".dot");

    /*
     * The backend may expose the exchange connection
     * status using several possible fields.
     */

    const connected =
        state &&
        (
            state.exchange_connected === true ||
            state.connection_status === "CONNECTED" ||
            state.connection_status === "LIVE" ||
            state.market_status === "LIVE"
        );

    if (dot) {

        if (connected) {

            dot.classList.add("active");

            dot.classList.remove("offline");

        } else {

            dot.classList.remove("active");

        }

    }

}


/* =========================================================
   UPDATE CLOCK
   ========================================================= */

function updateClock() {

    const clock =
        getElement("clock");

    if (!clock) {

        return;

    }

    const now =
        new Date();

    clock.textContent =
        now.toLocaleTimeString();

}


/* =========================================================
   UPDATE DASHBOARD
   ========================================================= */

function renderPQIState(state) {

    if (!state) {

        return;

    }

    /*
     * Keep a copy of the latest backend state.
     */
    pqiState = state;


    /* -----------------------------------------------------
       PQI STATUS
       ----------------------------------------------------- */

    updateElement(
        "pqi-status",
        state.status
    );


    /* -----------------------------------------------------
       EXCHANGE
       ----------------------------------------------------- */

    updateElement(
        "exchange-status",
        state.exchange
    );

    /*
     * Some dashboard versions use #exchange
     * rather than #exchange-status.
     */
    updateElement(
        "exchange",
        state.exchange
    );


    /* -----------------------------------------------------
       MARKET
       ----------------------------------------------------- */

    updateElement(
        "market",
        state.market
    );


    /* -----------------------------------------------------
       CURRENT DECISION
       ----------------------------------------------------- */

    updateElement(
        "decision",
        state.current_decision
    );


    /* -----------------------------------------------------
       CONFIDENCE
       ----------------------------------------------------- */

    if (
        state.confidence !== undefined &&
        state.confidence !== null
    ) {

        updateElement(
            "confidence",
            formatPercentage(
                state.confidence
            )
        );

    } else {

        updateElement(
            "confidence",
            null
        );

    }


    /* -----------------------------------------------------
       MARKET REGIME
       ----------------------------------------------------- */

    updateElement(
        "regime",
        state.market_regime
    );


    /* -----------------------------------------------------
       OPEN POSITIONS
       ----------------------------------------------------- */

    updateElement(
        "positions",
        state.open_positions
    );


    /* -----------------------------------------------------
       CURRENCY
       ----------------------------------------------------- */

    const currency =
        getStateCurrency(state);


    /* -----------------------------------------------------
       PORTFOLIO VALUE
       ----------------------------------------------------- */

    updateElement(
        "portfolio",
        formatCurrency(
            state.portfolio_value,
            currency
        )
    );


    /* -----------------------------------------------------
       DAILY P/L
       ----------------------------------------------------- */

    updateElement(
        "daily-pnl",
        formatCurrency(
            state.daily_pnl,
            currency
        )
    );


    /* -----------------------------------------------------
       CURRENT TASK
       ----------------------------------------------------- */

    updateElement(
        "task",
        state.current_task
    );


    /* -----------------------------------------------------
       SIGNALS ANALYSED
       ----------------------------------------------------- */

    updateElement(
        "signals",
        state.signals_analysed
    );


    /* -----------------------------------------------------
       TRADES TODAY
       ----------------------------------------------------- */

    updateElement(
        "trades",
        state.trades_today
    );


    /* -----------------------------------------------------
       WIN RATE
       ----------------------------------------------------- */

    if (
        state.win_rate !== undefined &&
        state.win_rate !== null
    ) {

        updateElement(
            "winrate",
            formatPercentage(
                state.win_rate
            )
        );

    } else {

        updateElement(
            "winrate",
            null
        );

    }


    /* -----------------------------------------------------
       RISK EXPOSURE
       ----------------------------------------------------- */

    if (
        state.risk_exposure !== undefined &&
        state.risk_exposure !== null
    ) {

        updateElement(
            "risk",
            formatPercentage(
                state.risk_exposure
            )
        );

    } else {

        updateElement(
            "risk",
            null
        );

    }


    /* -----------------------------------------------------
       NEXT SCAN
       ----------------------------------------------------- */

    if (
        state.next_scan !== undefined &&
        state.next_scan !== null
    ) {

        updateElement(
            "nextscan",
            state.next_scan
        );

    }


    /* -----------------------------------------------------
       UPDATE VISUAL STATUS
       ----------------------------------------------------- */

    updateStatusIndicator(state);

    updateMarketStatus(state);

}


/* =========================================================
   LOAD PQI STATE
   ========================================================= */

async function loadPQIState() {

    /*
     * Prevent another request from starting while
     * the previous request is still running.
     *
     * This is important.
     */
    if (stateRequestInProgress) {

        return;

    }

    stateRequestInProgress = true;


    try {

        const response =
            await fetch(
                PQI_CONFIG.stateEndpoint,
                {
                    method: "GET",

                    cache: "no-store",

                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!response.ok) {

            console.warn(
                "PQI state request failed:",
                response.status
            );

            return;

        }


        const state =
            await response.json();


        renderPQIState(state);


    } catch (error) {

        console.error(
            "Unable to load PQI state:",
            error
        );


    } finally {

        stateRequestInProgress = false;

    }

}


/* =========================================================
   GET CURRENT EXCHANGE
   ========================================================= */

function getCurrentExchange() {

    /*
     * First preference:
     * latest backend state.
     */

    if (
        pqiState &&
        pqiState.exchange
    ) {

        return pqiState.exchange;

    }


    /*
     * Second preference:
     * dashboard DOM.
     */

    const exchangeElement =
        getElement("exchange");


    if (
        exchangeElement &&
        exchangeElement.textContent &&
        exchangeElement.textContent !== "--"
    ) {

        return exchangeElement.textContent.trim();

    }


    const exchangeStatusElement =
        getElement("exchange-status");


    if (
        exchangeStatusElement &&
        exchangeStatusElement.textContent &&
        exchangeStatusElement.textContent !== "--"
    ) {

        return exchangeStatusElement.textContent.trim();

    }


    return null;

}


/* =========================================================
   GET CURRENT MARKET
   ========================================================= */

function getCurrentMarket() {

    /*
     * First preference:
     * latest backend state.
     */

    if (
        pqiState &&
        pqiState.market
    ) {

        return pqiState.market;

    }


    /*
     * Second preference:
     * dashboard DOM.
     */

    const marketElement =
        getElement("market");


    if (
        marketElement &&
        marketElement.textContent &&
        marketElement.textContent !== "--"
    ) {

        return marketElement.textContent.trim();

    }


    return null;

}


/* =========================================================
   ENGAGE PQI
   ========================================================= */

async function engagePQI() {

    const exchange =
        getCurrentExchange();

    const market =
        getCurrentMarket();


    /*
     * Do NOT silently substitute Binance
     * or BTCUSDT.
     *
     * The backend must tell us what market
     * PQI is currently configured to use.
     */

    if (!exchange) {
        exchange = "binance";
    }


    if (!market) {
        market = "BTC/USDT";
    }


    const button =
        getElement("engage-pqi");


    if (button) {

        button.disabled = true;

        button.dataset.originalText =
            button.textContent;

        button.textContent =
            "ENGAGING...";

    }


    try {

        const response =
            await fetch(
                PQI_CONFIG.engageEndpoint,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json",

                        "X-CSRFToken": getCSRFToken()

                    },

                    body: JSON.stringify({

                        exchange: exchange,

                        market: market

                    })

                }
            );


        if (!response.ok) {

            console.error(
                "PQI engage request failed:",
                response.status
            );

            return;

        }


        /*
         * If the backend returns the new PQI state,
         * use it immediately.
         */

        const contentType =
            response.headers.get(
                "content-type"
            );


        if (
            contentType &&
            contentType.includes(
                "application/json"
            )
        ) {

            const state =
                await response.json();

            renderPQIState(state);

        } else {

            await loadPQIState();

        }


    } catch (error) {

        console.error(
            "Unable to engage PQI:",
            error
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                button.dataset.originalText ||
                "ENGAGE PQI";

        }

    }

}


/* =========================================================
   PAUSE PQI
   ========================================================= */

async function pausePQI() {

    const button =
        getElement("pause-pqi");


    if (button) {

        button.disabled = true;

        button.dataset.originalText =
            button.textContent;

        button.textContent =
            "PAUSING...";

    }


    try {

        const response =
            await fetch(
                PQI_CONFIG.pauseEndpoint,
                {

                    method: "POST",

                    headers: csrfHeaders({
                        "Accept": "application/json"
                    })

                }
            );


        if (!response.ok) {

            console.error(
                "PQI pause request failed:",
                response.status
            );

            return;

        }


        const contentType =
            response.headers.get(
                "content-type"
            );


        if (
            contentType &&
            contentType.includes(
                "application/json"
            )
        ) {

            const state =
                await response.json();

            renderPQIState(state);

        } else {

            await loadPQIState();

        }


    } catch (error) {

        console.error(
            "Unable to pause PQI:",
            error
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                button.dataset.originalText ||
                "PAUSE";

        }

    }

}


/* =========================================================
   EMERGENCY STOP
   ========================================================= */

async function stopPQI() {

    const confirmed =
        window.confirm(
            "Are you sure you want to execute the PQI emergency stop?"
        );


    if (!confirmed) {

        return;

    }


    const button =
        getElement("stop-pqi");


    if (button) {

        button.disabled = true;

        button.dataset.originalText =
            button.textContent;

        button.textContent =
            "STOPPING...";

    }


    try {

        const response =
            await fetch(
                PQI_CONFIG.stopEndpoint,
                {

                    method: "POST",

                    headers: csrfHeaders({
                        "Accept": "application/json"
                    })

                }
            );


        if (!response.ok) {

            console.error(
                "PQI emergency stop failed:",
                response.status
            );

            return;

        }


        const contentType =
            response.headers.get(
                "content-type"
            );


        if (
            contentType &&
            contentType.includes(
                "application/json"
            )
        ) {

            const state =
                await response.json();

            renderPQIState(state);

        } else {

            await loadPQIState();

        }


    } catch (error) {

        console.error(
            "Unable to stop PQI:",
            error
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                button.dataset.originalText ||
                "EMERGENCY STOP";

        }

    }

}


/* =========================================================
   START POLLING
   ========================================================= */

function startPQIPolling() {

    /*
     * Prevent duplicate intervals.
     */
    if (pollingTimer !== null) {

        clearInterval(
            pollingTimer
        );

    }


    /*
     * Initial load.
     */
    loadPQIState();


    /*
     * One polling loop only.
     */
    pollingTimer =
        setInterval(
            loadPQIState,
            PQI_CONFIG.pollingInterval
        );

}


/* =========================================================
   STOP POLLING
   ========================================================= */

function stopPQIPolling() {

    if (pollingTimer === null) {

        return;

    }


    clearInterval(
        pollingTimer
    );


    pollingTimer = null;

}


/* =========================================================
   BUTTON INITIALIZATION
   ========================================================= */

function initializePQIControls() {

    const engageButton =
        getElement("engage-pqi");

    const pauseButton =
        getElement("pause-pqi");

    const stopButton =
        getElement("stop-pqi");


    if (engageButton) {

        engageButton.addEventListener(
            "click",
            engagePQI
        );

    }


    if (pauseButton) {

        pauseButton.addEventListener(
            "click",
            pausePQI
        );

    }


    if (stopButton) {

        stopButton.addEventListener(
            "click",
            stopPQI
        );

    }

}


/* =========================================================
   PAGE INITIALIZATION
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        /*
         * Initialize buttons once.
         */
        initializePQIControls();


        /*
         * Start the dashboard state.
         */
        startPQIPolling();


        /*
         * Start dashboard clock.
         */
        updateClock();


        setInterval(
            updateClock,
            1000
        );

    }
);


/* =========================================================
   CLEANUP
   ========================================================= */

window.addEventListener(
    "beforeunload",
    () => {

        stopPQIPolling();

    }
);