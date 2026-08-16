/*
 * PQI Live UI Helpers
 *
 * This file intentionally does NOT poll /api/pqi/state.
 * pqi.js owns dashboard state polling.
 */


function setPQILiveStatus(status) {

    const element =
        document.querySelector(".market-status");

    if (!element) {
        return;
    }

    const dot =
        element.querySelector(".dot");

    if (status === "ACTIVE" || status === "RUNNING") {

        if (dot) {
            dot.classList.add("active");
        }

        element.classList.add("active");

        return;
    }

    if (dot) {
        dot.classList.remove("active");
    }

    element.classList.remove("active");
}