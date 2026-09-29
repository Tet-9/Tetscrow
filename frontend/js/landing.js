// Landing-page behaviour: live stats, how-it-works tabs, press carousel.
(function () {
  "use strict";
  var S = window.TET_SITE || { press: [] };
  var C = window.TET_CONFIG || {};
  var T = window.TetSite;

  // ---- live user count (real number from the backend, never hard-coded) ----
  var usersEl = document.getElementById("stat-users");
  fetch(C.API_BASE + "/stats")
    .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
    .then(function (s) { usersEl.textContent = Number(s.users_registered).toLocaleString(); })
    .catch(function () { usersEl.textContent = "-"; });

  var infoBtn = document.getElementById("stat-info");
  var pop = document.getElementById("stat-pop");
  infoBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    pop.classList.toggle("show");
  });
  document.addEventListener("click", function () { pop.classList.remove("show"); });

  // ---- how it works ----
  var STEP_ART =
    '<svg class="step-art" viewBox="0 0 220 200" aria-hidden="true">' +
    '<ellipse cx="110" cy="182" rx="80" ry="12" fill="#000" opacity=".12"/>' +
    '<rect x="42" y="34" width="112" height="132" rx="14" fill="#fff" stroke="#0a0a0a" stroke-width="5"/>' +
    '<rect x="70" y="18" width="112" height="132" rx="14" fill="#6a3df0" stroke="#0a0a0a" stroke-width="5"/>' +
    '<path d="M100 84l18 18 34-38" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>' +
    '</svg>';

  var STEPS = [
    { tag: "STEP 1", label: "Create a contract between parties", title: "Create A Mutual Agreement",
      text: "The agreement can be anything between you and the other party. Tet's smart contract is the neutral medium that keeps it safe and fair for both sides." },
    { tag: "STEP 2", label: "Client pays to the escrow", title: "Fund The Escrow",
      text: "The sender deposits the agreed amount into the Tet contract. The funds are locked on-chain, visible to both parties, and out of reach until the deal resolves." },
    { tag: "STEP 3", label: "Service or RWA gets delivered", title: "Delivery",
      text: "The receiver delivers the service or real-world asset, then marks it delivered in the app. Marking delivery also starts the auto-release timer." },
    { tag: "STEP 4A (Finished)", label: "Client releases the payment", title: "Release The Payment",
      text: "Happy with the delivery? The sender releases the payment and the funds go straight to the receiver. If the sender goes silent, auto-release pays the receiver once the window ends." },
    { tag: "STEP 4B (Rare Cases)", label: "Any party can raise a dispute", title: "Raise A Dispute",
      text: "If something goes wrong, either party can freeze the funds by raising a dispute. The assigned arbiter reviews the case and sends the funds to the rightful party." }
  ];

  var list = document.getElementById("steps");
  var card = document.getElementById("step-card");
  list.innerHTML = STEPS.map(function (s, i) {
    return '<button class="step' + (i === 0 ? " active" : "") + '" data-i="' + i + '" aria-pressed="' + (i === 0) + '">' +
      '<span class="step-icon"></span><span><small>' + s.tag + '</small><strong>' + s.label + '</strong></span></button>';
  }).join("");

  function showStep(i) {
    var s = STEPS[i];
    card.innerHTML =
      '<div class="step-card-top"><h3>' + s.title + '</h3>' + STEP_ART + '</div>' +
      '<p>' + s.text + '</p>' +
      '<div class="btn-row">' +
        '<a class="btn btn-outline" href="#" data-link="docs">Learn More <span class="arrow"></span></a>' +
        '<a class="btn btn-dark" href="#" data-link="video">Watch A Video <span class="arrow"></span></a>' +
      '</div>';
    T.wireLinks(card);
    list.querySelectorAll(".step").forEach(function (b) {
      var on = Number(b.getAttribute("data-i")) === i;
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", String(on));
    });
  }
  list.addEventListener("click", function (e) {
    var b = e.target.closest(".step");
    if (b) showStep(Number(b.getAttribute("data-i")));
  });
  showStep(0);

  // ---- press carousel ----
  var track = document.getElementById("press-track");
  var MK = '<svg viewBox="0 0 32 32" aria-hidden="true"><polygon points="16,2 2,25 19,30" fill="currentColor"/><polygon points="16,2 19,30 30,21" fill="currentColor" opacity=".55"/></svg>';
  var items = S.press || [];
  track.innerHTML = items.map(function (p) {
    var has = p.url && p.url.trim();
    return '<a class="pcard" href="' + (has ? T.esc(p.url) : "#") + '"' + (has ? ' target="_blank" rel="noopener noreferrer"' : ' data-pending="1"') + '>' +
      '<div class="pcard-art"><h4 class="pcard-head">' + T.esc(p.art || "") + '</h4>' +
      (p.vertical ? '<span class="pcard-vert">' + T.esc(p.vertical) + ' &darr;</span>' : "") +
      '<div class="hawk-slot" data-scene="' + T.esc(p.scene) + '" data-img="assets/hawk-' + T.esc(p.scene) + '.png"></div>' +
      '<span class="pcard-logo">' + MK + 'TET</span></div>' +
      '<h3 class="pcard-title">' + T.esc(p.title || "") + '</h3>' + (has ? "" : '<span class="pcard-soon">Coming soon</span>') + '</a>';
  }).join("");
  track.querySelectorAll("[data-pending]").forEach(function (a) {
    a.addEventListener("click", function (e) { e.preventDefault(); T.toast("This article isn't published yet. Add its link in js/site-config.js."); });
  });
  if (window.Hawk3D) { window.Hawk3D.scan(track); }
  function scrollPress(dir) {
    track.scrollBy({ left: dir * Math.max(track.clientWidth * 0.8, 300), behavior: "smooth" });
  }
  document.getElementById("press-prev").addEventListener("click", function () { scrollPress(-1); });
  document.getElementById("press-next").addEventListener("click", function () { scrollPress(1); });
})();
