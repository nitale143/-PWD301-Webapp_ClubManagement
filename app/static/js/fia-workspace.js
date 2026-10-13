(() => {
    const toggle = document.querySelector(".fia-mobile-menu");
    const sidebar = document.getElementById("fia-sidebar");
    const scrim = document.querySelector(".fia-sidebar-scrim");

    if (!toggle || !sidebar || !scrim) return;

    const mobileViewport = window.matchMedia("(max-width: 760px)");

    const syncSidebarAccess = () => {
        if (!mobileViewport.matches) {
            sidebar.inert = false;
            sidebar.removeAttribute("aria-hidden");
            return;
        }

        const isOpen = document.body.classList.contains("fia-menu-open");
        sidebar.inert = !isOpen;
        sidebar.setAttribute("aria-hidden", String(!isOpen));
    };

    const setMenuOpen = (isOpen, restoreFocus = false) => {
        document.body.classList.toggle("fia-menu-open", isOpen);
        toggle.setAttribute("aria-expanded", String(isOpen));
        toggle.setAttribute("aria-label", isOpen ? "Đóng điều hướng" : "Mở điều hướng");
        syncSidebarAccess();

        if (restoreFocus) toggle.focus();
        if (isOpen) sidebar.querySelector(".fia-primary-nav a")?.focus();
    };

    syncSidebarAccess();

    toggle.addEventListener("click", () => {
        setMenuOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    scrim.addEventListener("click", () => setMenuOpen(false, true));
    sidebar.addEventListener("click", (event) => {
        if (event.target.closest("a")) setMenuOpen(false);
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && document.body.classList.contains("fia-menu-open")) {
            setMenuOpen(false, true);
        }
    });

    mobileViewport.addEventListener("change", (event) => {
        if (!event.matches) setMenuOpen(false);
        syncSidebarAccess();
    });
})();
