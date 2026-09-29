// Plays a pre-rendered frame sequence when the pointer is over its card, and eases back to the still frame when it leaves.
//   <div class="sprite" data-frames="../assets/hero/f%03d.webp" data-count="40" data-hover-host>
(function () {
  "use strict";
  function pad(n, w) { n = String(n); while (n.length < w) { n = "0" + n; } return n; }
  function mount(el) {
    var pattern = el.getAttribute("data-frames"), count = Number(el.getAttribute("data-count")) || 1;
    var host = el.closest("[data-hover-host]") || el;
    var frames = [], loaded = 0, cv = document.createElement("canvas"), ctx = cv.getContext("2d");
    cv.setAttribute("role", "img");
    cv.setAttribute("aria-label", el.getAttribute("aria-label") || "Animated Tet hawk");
    el.appendChild(cv);
    for (var i = 0; i < count; i++) {
      (function (i) {
        var im = new Image();
        im.onload = function () {
          loaded++;
          if (i === 0) { cv.width = im.naturalWidth; cv.height = im.naturalHeight; draw(0); }
        };
        im.src = pattern.replace(/%0(\d)d/, function (m, w) { return pad(i, Number(w)); });
        frames.push(im);
      })(i);
    }
    function draw(pos) {
      var a = Math.floor(pos), f = pos - a, b = Math.min(a + 1, count - 1);
      ctx.clearRect(0, 0, cv.width, cv.height);
      if (frames[a] && frames[a].complete && frames[a].naturalWidth) { ctx.globalAlpha = 1; ctx.drawImage(frames[a], 0, 0); }
      if (f > 0.02 && frames[b] && frames[b].complete && frames[b].naturalWidth) { ctx.globalAlpha = f; ctx.drawImage(frames[b], 0, 0); }
      ctx.globalAlpha = 1;
    }
    var pos = 0, dir = 1, hover = false, hold = 0, last = performance.now(), running = false;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function tick(now) {
      var dt = Math.min((now - last) / 1000, 0.1); last = now;
      if (hover && !reduce) {
        if (hold > 0) { hold -= dt; } else {
          pos += dir * dt * 10;
          if (pos >= count - 1) { pos = count - 1; dir = -1; hold = 0.7; }
          if (pos <= 0) { pos = 0; dir = 1; hold = 0.5; }
        }
      } else if (pos > 0) {
        pos = Math.max(0, pos - dt * 36); dir = 1; hold = 0;
      }
      draw(pos);
      if (hover || pos > 0) { requestAnimationFrame(tick); } else { running = false; }
    }
    function go() { if (!running && loaded > count * 0.9) { running = true; last = performance.now(); requestAnimationFrame(tick); } }
    host.addEventListener("pointerenter", function () { hover = true; go(); });
    host.addEventListener("pointerleave", function () { hover = false; go(); });
    host.addEventListener("click", function () { hover = !hover; go(); });
  }
  document.querySelectorAll(".sprite").forEach(mount);
})();
