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