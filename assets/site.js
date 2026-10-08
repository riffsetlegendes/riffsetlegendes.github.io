/* Riffs & Légendes : visuels de secours et lecteur Spotify intégré. */
(function () {
  "use strict";

  /* ---------- Visuels : si une image ne charge pas, on affiche une pochette typographique */
  function fallback(img) {
    var box = img.parentNode;
    if (!box || box.classList.contains("type-cover")) return;
    img.remove();
    box.classList.add("type-cover");
    var cat = document.createElement("span");
    cat.className = "tc-cat";
    cat.textContent = box.getAttribute("data-cat") || "";
    var year = document.createElement("span");
    year.className = "tc-year";
    year.textContent = box.getAttribute("data-label") || "";
    box.appendChild(cat);
    box.appendChild(year);
  }
  document.querySelectorAll(".riso img").forEach(function (img) {
    if (img.complete && img.naturalWidth === 0) fallback(img);
    else img.addEventListener("error", function () { fallback(img); });
  });

  /* ---------- Transition : la pochette cliquée glisse vers la couverture de l'article */
  document.addEventListener("click", function (ev) {
    var link = ev.target.closest("a.card-link, a.record");
    if (!link) return;
    var sl = link.querySelector(".sleeve");
    if (sl) sl.style.viewTransitionName = "cover";
  });
  window.addEventListener("pageshow", function () {
    document.querySelectorAll(".card-link .sleeve, .record .sleeve").forEach(function (s) { s.style.viewTransitionName = ""; });
  });

  /* ---------- Lecteur */
  var dock = document.getElementById("dock");
  if (!dock) return;
  var titleEl = dock.querySelector(".dock-title");
  var artistEl = dock.querySelector(".dock-artist");
  var controller = null, apiLoading = false, pending = null;
  var queue = [], index = -1, lastPos = 0, advancing = false;

  function loadApi(cb) {
    if (controller) return cb();
    pending = cb;
    if (apiLoading) return;
    apiLoading = true;
    window.onSpotifyIframeApiReady = function (api) {
      var first = queue[index];
      api.createController(document.getElementById("spotify-embed"),
        { uri: first ? first.dataset.uri : "", width: "100%", height: 80 },
        function (ctrl) {
          controller = ctrl;
          ctrl.addListener("ready", function () { ctrl.play(); });
          ctrl.addListener("playback_update", onUpdate);
          if (pending) { var p = pending; pending = null; p(true); }
        });
    };
    var s = document.createElement("script");
    s.src = "https://open.spotify.com/embed/iframe-api/v1";
    s.async = true;
    document.body.appendChild(s);
  }

  function mark() {
    document.querySelectorAll(".tl-row.is-current").forEach(function (b) { b.classList.remove("is-current"); });
    var b = queue[index];
    if (b) b.classList.add("is-current");
  }

  function play(i) {
    if (i < 0 || i >= queue.length) return;
    index = i;
    lastPos = 0;
    advancing = false;
    var b = queue[i];
    titleEl.textContent = b.dataset.title;
    artistEl.textContent = b.dataset.artist;
    dock.hidden = false;
    document.body.classList.add("has-dock");
    mark();
    loadApi(function (fresh) {
      if (!fresh) {
        controller.loadUri(b.dataset.uri);
        setTimeout(function () { controller.play(); }, 350);
      }
    });
  }

  function onUpdate(e) {
    var d = e.data || {};
    var playing = !d.isPaused && !d.isBuffering;
    dock.classList.toggle("is-playing", playing);
    var cur = queue[index];
    if (cur) cur.classList.toggle("is-playing", playing);
    if (!d.isPaused) lastPos = d.position;
    if (d.isPaused && d.duration > 0 && lastPos >= d.duration - 1500 && !advancing) {
      advancing = true;
      if (index < queue.length - 1) play(index + 1);
    }
  }

  function queueFrom(el) {
    var scope = el.closest("[data-queue]") || document;
    return Array.prototype.slice.call(scope.querySelectorAll("button.tl-row[data-uri]"));
  }

  document.addEventListener("click", function (ev) {
    var row = ev.target.closest("button.tl-row[data-uri]");
    if (row) {
      if (row.classList.contains("is-current") && controller) { controller.togglePlay(); return; }
      queue = queueFrom(row);
      play(queue.indexOf(row));
      return;
    }
    var all = ev.target.closest("[data-play-all]");
    if (all) {
      queue = queueFrom(all);
      play(0);
      return;
    }
    var act = ev.target.closest(".dock-btn");
    if (act) {
      var a = act.dataset.act;
      if (a === "next") play(Math.min(index + 1, queue.length - 1));
      if (a === "prev") play(Math.max(index - 1, 0));
      if (a === "close") {
        if (controller) controller.pause();
        dock.hidden = true;
        document.body.classList.remove("has-dock");
        dock.classList.remove("is-playing");
        document.querySelectorAll(".tl-row.is-current").forEach(function (b) { b.classList.remove("is-current", "is-playing"); });
      }
    }
  });
})();
