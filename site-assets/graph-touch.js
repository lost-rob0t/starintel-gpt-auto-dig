(() => {
  "use strict";

  const canvas = document.getElementById("graph-canvas");
  const shell = document.getElementById("graph-shell");
  if (!canvas || !shell || canvas.dataset.mobileZoom === "true") return;

  canvas.dataset.mobileZoom = "true";
  canvas.style.touchAction = "none";
  canvas.style.overscrollBehavior = "contain";
  canvas.style.webkitUserSelect = "none";
  canvas.style.userSelect = "none";

  const style = document.createElement("style");
  style.textContent = `
    .graph-mobile-zoom {
      position: absolute;
      top: .65rem;
      left: .65rem;
      z-index: 5;
      display: none;
      flex-direction: column;
      gap: .35rem;
    }
    .graph-mobile-zoom button {
      width: 2.75rem;
      height: 2.75rem;
      border: 1px solid #4c6685;
      border-radius: .65rem;
      background: #07111fe8;
      color: #f8fafc;
      font: 700 1.35rem/1 system-ui;
      box-shadow: 0 .35rem 1rem #0008;
      touch-action: manipulation;
    }
    .graph-mobile-zoom button:active {
      background: #17304e;
      transform: scale(.96);
    }
    @media (hover: none), (pointer: coarse) {
      .graph-mobile-zoom { display: flex; }
    }
  `;
  document.head.appendChild(style);

  const zoomControls = document.createElement("div");
  zoomControls.className = "graph-mobile-zoom";
  zoomControls.innerHTML = `
    <button type="button" data-zoom="in" aria-label="Zoom graph in">+</button>
    <button type="button" data-zoom="out" aria-label="Zoom graph out">−</button>
  `;
  shell.appendChild(zoomControls);

  const state = {
    pinching: false,
    distance: 0,
    accumulator: 0
  };

  function midpoint(touches) {
    const first = touches[0];
    const second = touches[1];
    return {
      clientX: (first.clientX + second.clientX) / 2,
      clientY: (first.clientY + second.clientY) / 2
    };
  }

  function distance(touches) {
    const first = touches[0];
    const second = touches[1];
    return Math.hypot(second.clientX - first.clientX, second.clientY - first.clientY);
  }

  function emitZoom(deltaY, point) {
    canvas.dispatchEvent(new WheelEvent("wheel", {
      bubbles: false,
      cancelable: true,
      clientX: point.clientX,
      clientY: point.clientY,
      deltaMode: WheelEvent.DOM_DELTA_PIXEL,
      deltaY
    }));
  }

  function cancelGraphDrag() {
    canvas.dispatchEvent(new Event("pointercancel", { bubbles: true, cancelable: true }));
  }

  function beginPinch(event) {
    if (event.touches.length < 2) return;
    state.pinching = true;
    state.distance = distance(event.touches);
    state.accumulator = 0;
    cancelGraphDrag();
    event.preventDefault();
  }

  canvas.addEventListener("touchstart", (event) => {
    if (event.touches.length >= 2) beginPinch(event);
  }, { passive: false });

  canvas.addEventListener("touchmove", (event) => {
    if (event.touches.length < 2) return;
    if (!state.pinching) beginPinch(event);
    event.preventDefault();

    const nextDistance = distance(event.touches);
    if (!state.distance || !nextDistance) {
      state.distance = nextDistance;
      return;
    }

    state.accumulator += Math.log(nextDistance / state.distance);
    state.distance = nextDistance;
    const point = midpoint(event.touches);
    const threshold = 0.065;
    let steps = 0;

    while (state.accumulator >= threshold && steps < 3) {
      emitZoom(-1, point);
      state.accumulator -= threshold;
      steps += 1;
    }
    while (state.accumulator <= -threshold && steps < 3) {
      emitZoom(1, point);
      state.accumulator += threshold;
      steps += 1;
    }
  }, { passive: false });

  function endPinch(event) {
    if (state.pinching) event.preventDefault();
    if (event.touches.length >= 2) {
      state.distance = distance(event.touches);
      return;
    }
    state.pinching = false;
    state.distance = 0;
    state.accumulator = 0;
  }

  canvas.addEventListener("touchend", endPinch, { passive: false });
  canvas.addEventListener("touchcancel", endPinch, { passive: false });

  zoomControls.addEventListener("click", (event) => {
    const button = event.target.closest("[data-zoom]");
    if (!button) return;
    const rect = canvas.getBoundingClientRect();
    emitZoom(button.dataset.zoom === "in" ? -1 : 1, {
      clientX: rect.left + rect.width / 2,
      clientY: rect.top + rect.height / 2
    });
  });

  requestAnimationFrame(() => {
    const help = document.querySelector(".graph-help");
    if (help) {
      help.textContent = "Drag nodes · drag empty space to pan · pinch or use +/− to zoom · double-click to open";
    }
  });
})();