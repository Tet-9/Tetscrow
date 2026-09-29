// Mascot images + the 3D Tet logo mark.
//   <div class="hawk-slot" data-scene="rocket" data-img="assets/hawk-rocket.png"> shows a pre-rendered 3D hawk image.
//   <span data-tet3d> becomes a small rotating 3D tetrahedron (three.js) and keeps a flat SVG if WebGL is unavailable.
(function () {
  "use strict";
  var THREE = window.THREE;
  var MARK = '<svg class="hawk-fallback" viewBox="0 0 32 32" aria-hidden="true"><polygon points="16,2 2,25 19,30" fill="currentColor"/><polygon points="16,2 19,30 30,21" fill="currentColor" opacity=".55"/></svg>';
  var webglOK = null;
  function hasWebGL() {
    if (webglOK !== null) { return webglOK; }
    try {
      var c = document.createElement("canvas");
      webglOK = !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl")));
    } catch (e) { webglOK = false; }
    return webglOK;
  }
  function col(hex) { return new THREE.Color(hex).convertSRGBToLinear(); }

  function mountSlot(el) {
    if (el.getAttribute("data-mounted")) { return; }
    el.setAttribute("data-mounted", "1");
    var src = el.getAttribute("data-img");
    if (!src) { return; }
    var im = new Image();
    im.alt = el.getAttribute("aria-label") || "";
    im.onload = function () { el.innerHTML = ""; el.appendChild(im); };
    im.onerror = function () { el.innerHTML = MARK; };
    im.src = src;
  }

  function mountMark(el) {
    if (el.getAttribute("data-mounted")) { return; }
    el.setAttribute("data-mounted", "1");
    if (!THREE || !hasWebGL()) { return; }
    try {
      var size = el.clientWidth || 44;
      var r = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      r.outputEncoding = THREE.sRGBEncoding;
      r.setClearColor(0x000000, 0);
      r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      r.setSize(size, size);
      var scene = new THREE.Scene();
      scene.add(new THREE.HemisphereLight(0xffffff, 0x6a3df0, 0.7));
      var l1 = new THREE.DirectionalLight(0xffffff, 1.4);
      l1.position.set(2, 3, 4);
      scene.add(l1);
      var l2 = new THREE.DirectionalLight(0x8a66ff, 1.6);
      l2.position.set(-3, -1, 2);
      scene.add(l2);
      var group = new THREE.Group();
      group.add(new THREE.Mesh(new THREE.TetrahedronGeometry(1.35), new THREE.MeshStandardMaterial({ color: col(0x0a0a0a), roughness: 0.3, metalness: 0.35, flatShading: true })));
      scene.add(group);
      var cam = new THREE.PerspectiveCamera(34, 1, 0.1, 50);
      cam.position.set(0, 0, 5);
      el.innerHTML = "";
      el.appendChild(r.domElement);
      var speed = 0.8, target = 0.8, ang = 0, last = performance.now();
      var host = el.parentNode || el;
      host.addEventListener("pointerenter", function () { target = 3.2; });
      host.addEventListener("pointerleave", function () { target = 0.8; });
      (function frame(now) {
        requestAnimationFrame(frame);
        var dt = Math.min((now - last) / 1000, 0.1);
        last = now;
        speed += (target - speed) * Math.min(1, dt * 4);
        ang += dt * speed;
        group.rotation.y = ang;
        group.rotation.x = 0.55 + Math.sin(ang * 0.7) * 0.2;
        group.position.y = Math.sin(ang * 1.3) * 0.06;
        r.render(scene, cam);
      })(last);
    } catch (e) { /* keeps the flat SVG mark */ }
  }

  function scan(root) {
    root = root || document;
    root.querySelectorAll(".hawk-slot").forEach(mountSlot);
    root.querySelectorAll("[data-tet3d]").forEach(mountMark);
  }

  window.Hawk3D = { scan: scan };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { scan(document); });
  } else {
    scan(document);
  }
})();
