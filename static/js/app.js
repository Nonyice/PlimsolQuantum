document.addEventListener("DOMContentLoaded", () => {

    const clock = document.getElementById("clock");

    if (clock) {

        setInterval(() => {

            clock.innerHTML = new Date().toLocaleTimeString();

        }, 1000);

    }

});