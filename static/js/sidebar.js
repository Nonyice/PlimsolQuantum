document.addEventListener("DOMContentLoaded", () => {
    const menu = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");
    const close = document.getElementById("sidebar-close");

    if (!menu || !sidebar) return;

    const closeSidebar = () => {
        sidebar.classList.remove("active");
        menu.setAttribute("aria-expanded", "false");
    };

    const openSidebar = () => {
        sidebar.classList.add("active");
        menu.setAttribute("aria-expanded", "true");
    };

    menu.setAttribute("aria-expanded", "false");

    menu.addEventListener("click", () => {
        if (sidebar.classList.contains("active")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    if (close) {
        close.addEventListener("click", closeSidebar);
    }

    sidebar.querySelectorAll(".nav-item").forEach((item) => {
        item.addEventListener("click", () => {
            if (window.matchMedia("(max-width: 768px)").matches) {
                closeSidebar();
            }
        });
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });
});
