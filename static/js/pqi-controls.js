/*
 * PQI Controls
 *
 * The selected exchange and market are NOT hard-coded here.
 *
 * The backend already knows the connected exchange and
 * active market, so ENGAGE simply asks PQI to use the
 * current configuration.
 */


async function engagePQI() {

    const button =
        document.getElementById("engage-pqi");

    if (button) {
        button.disabled = true;
    }

    try {

        const response =
            await fetch(
                "/api/pqi/engage",
                {
                    method: "POST",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!response.ok) {

            console.error(
                "PQI engage failed:",
                response.status
            );

            return;
        }


        /*
         * pqi.js will pick up the new state
         * through its normal polling cycle.
         */

        if (
            typeof loadPQIState ===
            "function"
        ) {

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
        }

    }
}


async function pausePQI() {

    try {

        const response =
            await fetch(
                "/api/pqi/pause",
                {
                    method: "POST",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!response.ok) {

            console.error(
                "PQI pause failed:",
                response.status
            );

            return;
        }


        if (
            typeof loadPQIState ===
            "function"
        ) {

            await loadPQIState();

        }

    } catch (error) {

        console.error(
            "Unable to pause PQI:",
            error
        );

    }
}


async function stopPQI() {

    try {

        const response =
            await fetch(
                "/api/pqi/stop",
                {
                    method: "POST",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!response.ok) {

            console.error(
                "PQI stop failed:",
                response.status
            );

            return;
        }


        if (
            typeof loadPQIState ===
            "function"
        ) {

            await loadPQIState();

        }

    } catch (error) {

        console.error(
            "Unable to stop PQI:",
            error
        );

    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        document
            .getElementById("engage-pqi")
            ?.addEventListener(
                "click",
                engagePQI
            );


        document
            .getElementById("pause-pqi")
            ?.addEventListener(
                "click",
                pausePQI
            );


        document
            .getElementById("stop-pqi")
            ?.addEventListener(
                "click",
                stopPQI
            );

    }
);