(() => {
  "use strict";

  const STORAGE_KEY = "starintel-theme";
  const DEFAULT_THEME = "midnight";
  const THEMES = Object.freeze([
    {
      id: "midnight", label: "Midnight", scheme: "dark",
      tokens: { bg: "#07111f", deep: "#030914", panel: "#0f1d2f", panel2: "#13243a", surface: "#0a1728", line: "#29415e", text: "#e2e8f0", strong: "#ffffff", muted: "#93a4b8", accent: "#38bdf8", accent2: "#7dd3fc", warm: "#f59e0b", danger: "#ef4444", success: "#22c55e", purple: "#a78bfa", pink: "#fb7185", orange: "#f97316", teal: "#14b8a6", blue: "#60a5fa", neutral: "#64748b" }
    },
    {
      id: "hacker-green", label: "Hacker Green", scheme: "dark",
      tokens: { bg: "#020805", deep: "#000f08", panel: "#06140d", panel2: "#0a1f13", surface: "#041009", line: "#1b6e3f", text: "#b7ffcc", strong: "#e5ffec", muted: "#69b985", accent: "#39ff88", accent2: "#8affb0", warm: "#d7ff45", danger: "#ff5c57", success: "#24d96e", purple: "#9cff57", pink: "#ff5c57", orange: "#a8ff60", teal: "#00f0a8", blue: "#57d7ff", neutral: "#538a65" }
    },
    {
      id: "synthwave-outrun", label: "Synthwave Outrun", scheme: "dark",
      tokens: { bg: "#170c32", deep: "#0b0718", panel: "#202146", panel2: "#2b1d4c", surface: "#1a1238", line: "#92406e", text: "#f3f4f5", strong: "#ffffff", muted: "#c99abb", accent: "#2de2e6", accent2: "#f6019d", warm: "#fba922", danger: "#dd546e", success: "#62FF00", purple: "#9700cc", pink: "#f6019d", orange: "#fba922", teal: "#2de2e6", blue: "#92406e", neutral: "#92406e" }
    },
    {
      id: "black-gold", label: "Black & Gold", scheme: "dark",
      tokens: { bg: "#050505", deep: "#000000", panel: "#11100b", panel2: "#1b180d", surface: "#0c0b08", line: "#554413", text: "#f6e7ae", strong: "#fff7d6", muted: "#b7a569", accent: "#ffd000", accent2: "#ffe772", warm: "#ffae00", danger: "#ff4b32", success: "#d7b631", purple: "#b99620", pink: "#ff6b35", orange: "#ff8c00", teal: "#cfa800", blue: "#f1d45d", neutral: "#8e7a40" }
    },
    {
      id: "yotsuba-pol", label: "Yotsuba /pol/", scheme: "light",
      tokens: { bg: "#eef2ff", deep: "#d6daf0", panel: "#d6daf0", panel2: "#e5e9ff", surface: "#e9edff", line: "#b7c5d9", text: "#000000", strong: "#0f0c5d", muted: "#34345c", accent: "#789922", accent2: "#34345c", warm: "#d00000", danger: "#d00000", success: "#527a1c", purple: "#5f4b8b", pink: "#d00000", orange: "#a04000", teal: "#2b7a78", blue: "#34345c", neutral: "#70738b" }
    },
    {
      id: "nord", label: "Nord", scheme: "dark",
      tokens: { bg: "#2e3440", deep: "#242933", panel: "#3b4252", panel2: "#434c5e", surface: "#353b49", line: "#4c566a", text: "#d8dee9", strong: "#eceff4", muted: "#aeb8c8", accent: "#88c0d0", accent2: "#81a1c1", warm: "#ebcb8b", danger: "#bf616a", success: "#a3be8c", purple: "#b48ead", pink: "#bf616a", orange: "#d08770", teal: "#8fbcbb", blue: "#5e81ac", neutral: "#616e88" }
    },
    {
      id: "dracula", label: "Dracula", scheme: "dark",
      tokens: { bg: "#282a36", deep: "#191a21", panel: "#343746", panel2: "#44475a", surface: "#30323f", line: "#6272a4", text: "#f8f8f2", strong: "#ffffff", muted: "#b8b8c5", accent: "#8be9fd", accent2: "#ff79c6", warm: "#f1fa8c", danger: "#ff5555", success: "#50fa7b", purple: "#bd93f9", pink: "#ff79c6", orange: "#ffb86c", teal: "#8be9fd", blue: "#6272a4", neutral: "#6272a4" }
    },
    {
      id: "solarized-dark", label: "Solarized Dark", scheme: "dark",
      tokens: { bg: "#002b36", deep: "#001f27", panel: "#073642", panel2: "#0b4452", surface: "#05313c", line: "#586e75", text: "#eee8d5", strong: "#fdf6e3", muted: "#93a1a1", accent: "#2aa198", accent2: "#268bd2", warm: "#b58900", danger: "#dc322f", success: "#859900", purple: "#6c71c4", pink: "#d33682", orange: "#cb4b16", teal: "#2aa198", blue: "#268bd2", neutral: "#657b83" }
    },
    {
      id: "gruvbox", label: "Gruvbox", scheme: "dark",
      tokens: { bg: "#282828", deep: "#1d2021", panel: "#3c3836", panel2: "#504945", surface: "#32302f", line: "#665c54", text: "#ebdbb2", strong: "#fbf1c7", muted: "#bdae93", accent: "#83a598", accent2: "#8ec07c", warm: "#fabd2f", danger: "#fb4934", success: "#b8bb26", purple: "#d3869b", pink: "#fb4934", orange: "#fe8019", teal: "#8ec07c", blue: "#458588", neutral: "#7c6f64" }
    },
    {
      id: "paper", label: "Paper", scheme: "light",
      tokens: { bg: "#f4f1e8", deep: "#e7e1d2", panel: "#fffdf7", panel2: "#ede7d8", surface: "#faf7ee", line: "#c9c0ad", text: "#27231c", strong: "#12100d", muted: "#6f6759", accent: "#315c7d", accent2: "#6d3f70", warm: "#a35f00", danger: "#a12622", success: "#477a47", purple: "#6d3f70", pink: "#a12622", orange: "#a35f00", teal: "#28766a", blue: "#315c7d", neutral: "#777064" }
    }
  ]);
  const THEME_MAP = new Map(THEMES.map((theme) => [theme.id, theme]));
  const currentScript = document.currentScript;

  function storedTheme() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return THEME_MAP.has(value) ? value : DEFAULT_THEME;
    } catch (_) {
      return DEFAULT_THEME;
    }
  }

  function persist(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {
      // Storage may be blocked in local file previews or strict privacy modes.
    }
  }

  function applyTokens(theme) {
    const root = document.documentElement;
    const tokens = theme.tokens;
    root.style.colorScheme = theme.scheme;
    root.style.setProperty("--bg", tokens.bg);
    root.style.setProperty("--bg-deep", tokens.deep);
    root.style.setProperty("--panel", tokens.panel);
    root.style.setProperty("--panel-2", tokens.panel2);
    root.style.setProperty("--surface", tokens.surface);
    root.style.setProperty("--line", tokens.line);
    root.style.setProperty("--text", tokens.text);
    root.style.setProperty("--text-strong", tokens.strong);
    root.style.setProperty("--muted", tokens.muted);
    root.style.setProperty("--accent", tokens.accent);
    root.style.setProperty("--accent-2", tokens.accent2);
    root.style.setProperty("--warm", tokens.warm);
    root.style.setProperty("--danger", tokens.danger);
    root.style.setProperty("--success", tokens.success);
    root.style.setProperty("--purple", tokens.purple);
    root.style.setProperty("--pink", tokens.pink);
    root.style.setProperty("--orange", tokens.orange);
    root.style.setProperty("--teal", tokens.teal);
    root.style.setProperty("--blue", tokens.blue);
    root.style.setProperty("--neutral", tokens.neutral);
  }

  function updateThemeColor(theme) {
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "theme-color";
      document.head.appendChild(meta);
    }
    meta.content = theme.tokens.bg;
  }

  function applyTheme(themeId) {
    const theme = THEME_MAP.get(themeId) || THEME_MAP.get(DEFAULT_THEME);
    document.documentElement.dataset.theme = theme.id;
    applyTokens(theme);
    persist(theme.id);
    updateThemeColor(theme);
    window.dispatchEvent(new CustomEvent("starintel:themechange", { detail: { theme: theme.id } }));
    return theme.id;
  }

  function mountPicker() {
    const header = document.querySelector("header");
    if (!header || document.getElementById("theme-select")) return;
    let nav = header.querySelector("nav");
    if (!nav) {
      nav = document.createElement("nav");
      header.appendChild(nav);
    }
    const label = document.createElement("label");
    label.className = "theme-picker";
    label.htmlFor = "theme-select";
    const caption = document.createElement("span");
    caption.textContent = "Theme";
    const select = document.createElement("select");
    select.id = "theme-select";
    select.setAttribute("aria-label", "Color theme");
    THEMES.forEach((theme) => {
      const option = document.createElement("option");
      option.value = theme.id;
      option.textContent = theme.label;
      select.appendChild(option);
    });
    select.value = document.documentElement.dataset.theme || DEFAULT_THEME;
    select.addEventListener("change", () => applyTheme(select.value));
    label.append(caption, select);
    nav.appendChild(label);
  }

  function loadCommunityFooter() {
    if (document.querySelector("script[data-starintel-community-footer]")) return;
    const script = document.createElement("script");
    const assetBase = currentScript?.src ? new URL(".", currentScript.src) : new URL(".", document.baseURI);
    script.src = new URL("starintel-community-footer.js", assetBase).href;
    script.defer = true;
    script.dataset.starintelCommunityFooter = "true";
    document.head.appendChild(script);
  }

  const activeTheme = applyTheme(storedTheme());
  loadCommunityFooter();
  window.StarIntelThemes = Object.freeze({
    themes: THEMES,
    active: () => document.documentElement.dataset.theme || activeTheme,
    apply: applyTheme
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountPicker, { once: true });
  else mountPicker();
})();
