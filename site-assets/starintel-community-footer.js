(() => {
  "use strict";

  const FOOTER_ID = "starintel-community-footer";
  const STYLE_ID = "starintel-community-footer-styles";
  const INVITE_URL = "https://discord.gg/R3VY8wr86Y";

  function installStyles() {
    if (document.getElementById(STYLE_ID)) return;

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .starintel-community-footer {
        position: relative;
        isolation: isolate;
        width: 100%;
        padding: 1.1rem clamp(1rem, 3vw, 2.5rem) calc(1.1rem + env(safe-area-inset-bottom));
        overflow: hidden;
        border-top: 1px solid var(--line, #29415e);
        background: var(--panel, #0b192a);
        background:
          radial-gradient(circle at 85% 0%, color-mix(in srgb, var(--accent, #38bdf8) 18%, transparent), transparent 32rem),
          linear-gradient(145deg, color-mix(in srgb, var(--panel, #0b192a) 94%, #000), var(--bg, #06101d));
        color: var(--text, #dbe7f4);
      }

      .starintel-community-footer::before {
        position: absolute;
        inset: 0 auto 0 0;
        width: 3px;
        content: "";
        background: var(--accent, #38bdf8);
        box-shadow: 0 0 24px color-mix(in srgb, var(--accent, #38bdf8) 65%, transparent);
      }

      .starintel-community-footer__inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.25rem;
        width: min(1500px, 100%);
        margin: 0 auto;
      }

      .starintel-community-footer__identity {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        min-width: 0;
      }

      .starintel-community-footer__mark {
        display: grid;
        flex: 0 0 auto;
        place-items: center;
        width: 2.45rem;
        height: 2.45rem;
        border: 1px solid color-mix(in srgb, var(--accent, #38bdf8) 72%, var(--line, #29415e));
        border-radius: 0.7rem;
        background: color-mix(in srgb, var(--accent, #38bdf8) 14%, var(--panel, #0b192a));
        color: var(--accent, #38bdf8);
        font-weight: 900;
        box-shadow: 0 0 28px color-mix(in srgb, var(--accent, #38bdf8) 17%, transparent);
      }

      .starintel-community-footer__copy {
        min-width: 0;
      }

      .starintel-community-footer__copy strong,
      .starintel-community-footer__copy span {
        display: block;
      }

      .starintel-community-footer__copy strong {
        color: var(--text-strong, var(--white, #f8fafc));
        font-size: 0.94rem;
        letter-spacing: 0.01em;
      }

      .starintel-community-footer__copy span {
        margin-top: 0.2rem;
        color: var(--muted, #8fa5bc);
        font-size: 0.78rem;
        line-height: 1.45;
      }

      .starintel-community-footer__action {
        display: inline-flex;
        flex: 0 0 auto;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        min-height: 2.55rem;
        padding: 0.62rem 0.9rem;
        border: 1px solid color-mix(in srgb, var(--accent, #38bdf8) 78%, var(--line, #29415e));
        border-radius: 0.7rem;
        background: color-mix(in srgb, var(--accent, #38bdf8) 15%, var(--panel, #0b192a));
        color: var(--text-strong, var(--white, #f8fafc));
        font-size: 0.84rem;
        font-weight: 800;
        text-decoration: none;
        box-shadow: 0 8px 28px color-mix(in srgb, var(--accent, #38bdf8) 10%, transparent);
        transition: transform 150ms ease, border-color 150ms ease, background 150ms ease;
      }

      .starintel-community-footer__action:hover {
        border-color: var(--accent, #38bdf8);
        background: color-mix(in srgb, var(--accent, #38bdf8) 24%, var(--panel, #0b192a));
        color: var(--text-strong, var(--white, #f8fafc));
        transform: translateY(-1px);
      }

      .starintel-community-footer__action:focus-visible {
        outline: 3px solid color-mix(in srgb, var(--accent, #38bdf8) 38%, transparent);
        outline-offset: 3px;
      }

      .starintel-community-footer__action svg {
        width: 1rem;
        height: 1rem;
        fill: none;
        stroke: currentColor;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 2;
      }

      @media (max-width: 760px) {
        .starintel-community-footer {
          padding-bottom: calc(4.75rem + env(safe-area-inset-bottom));
        }

        .starintel-community-footer__inner {
          align-items: stretch;
          flex-direction: column;
        }

        .starintel-community-footer__action {
          width: 100%;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .starintel-community-footer__action {
          transition: none;
        }
      }
    `;
    document.head.append(style);
  }

  function createFooter() {
    const footer = document.createElement("footer");
    footer.id = FOOTER_ID;
    footer.className = "starintel-community-footer";
    footer.setAttribute("aria-label", "StarIntel community");
    footer.innerHTML = `
      <div class="starintel-community-footer__inner">
        <div class="starintel-community-footer__identity">
          <span class="starintel-community-footer__mark" aria-hidden="true">✦</span>
          <span class="starintel-community-footer__copy">
            <strong>StarIntel Community</strong>
            <span>Research, actors, datasets, and development.</span>
          </span>
        </div>
        <a class="starintel-community-footer__action" href="${INVITE_URL}" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 8.5h10a3 3 0 0 1 3 3v3a3 3 0 0 1-3 3h-4l-3.5 2.5v-2.5H7a3 3 0 0 1-3-3v-3a3 3 0 0 1 3-3Z"/><path d="M9 13h.01M15 13h.01"/></svg>
          <span>Join Discord</span>
          <span aria-hidden="true">↗</span>
        </a>
      </div>
    `;
    return footer;
  }

  function placeFooter() {
    if (!document.body) return null;
    installStyles();

    let footer = document.getElementById(FOOTER_ID);
    if (!footer) footer = createFooter();
    if (footer.parentElement !== document.body || footer !== document.body.lastElementChild) {
      document.body.append(footer);
    }
    return footer;
  }

  function boot() {
    placeFooter();

    const observer = new MutationObserver(() => {
      const footer = document.getElementById(FOOTER_ID);
      if (!footer || footer !== document.body.lastElementChild) placeFooter();
    });
    observer.observe(document.body, { childList: true });
    window.addEventListener("pagehide", () => observer.disconnect(), { once: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
