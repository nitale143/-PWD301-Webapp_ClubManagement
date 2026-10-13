(() => {
  "use strict";

  document.addEventListener("click", (event) => {
    const origin = event.target instanceof Element ? event.target : event.target?.parentElement;
    const link = origin?.closest(".reference-landing a[data-landing-anchor]");
    if (!link) return;

    const fragment = link.getAttribute("href");
    if (!fragment || !fragment.startsWith("#")) return;

    let id;
    try {
      id = decodeURIComponent(fragment.slice(1));
    } catch {
      return;
    }
    const target = document.getElementById(id);
    if (!target) return;

    event.preventDefault();
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    target.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
    if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  });

  document.querySelectorAll("[data-avatar-image]").forEach((image) => {
    const hideBrokenImage = () => {
      image.hidden = true;
    };
    image.addEventListener("error", hideBrokenImage, { once: true });
    if (image.complete && image.naturalWidth === 0) hideBrokenImage();
  });
})();
