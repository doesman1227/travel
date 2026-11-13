// 「また行きたいところ」を地図に置く。場所・旅行の picks.html だけが読む。
// 共通の app.js は三セクションで同じ文面なので、地図はこちらに分けてある。
// 点になるのは、メモを持っていて（＝また行きたい）、座標も持っているものだけ。
// 座標は build_items.py の COORDS にある。近所の場所は住まいが分かるので座標を持たせない。
(() => {
  const box = document.getElementById("map");
  if (!box || !window.L) return;
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

  fetch("items.json", {cache: "no-cache"}).then(r => r.json()).then(data => {
    const spots = (data.items || []).filter(it => it.memo && it.lat && it.lng);
    if (!spots.length) { box.closest("section")?.remove(); return; }

    const map = L.map(box, {scrollWheelZoom: false});
    // 国土地理院の淡色地図。色が薄く、点が埋もれない。
    L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png", {
      attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>',
      minZoom: 4, maxZoom: 17,
    }).addTo(map);

    // 地図の絵は暗い配色のときも明るいままなので、点の色は明るい側の緑に固定する。
    const accent = "#2f6b5e";
    const marks = spots.map(it => {
      const name = it.url
        ? `<a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a>`
        : esc(it.title);
      const sub = [it.use, it.sub].filter(Boolean).map(esc).join("・");
      return L.circleMarker([it.lat, it.lng], {
        radius: 7, color: "#fff", weight: 2, fillColor: accent, fillOpacity: .9,
      }).bindPopup(`<b>${name}</b>${sub ? `<span>${sub}</span>` : ""}`)
        .bindTooltip(esc(it.title), {direction: "top", offset: [0, -6]});
    });
    const group = L.featureGroup(marks).addTo(map);
    map.fitBounds(group.getBounds().pad(0.08));

    // ページを縦に送る指やホイールを地図が奪わないように、一度触ってから拡大を許す。
    map.on("click", () => map.scrollWheelZoom.enable());
    box.addEventListener("mouseleave", () => map.scrollWheelZoom.disable());

    const n = document.querySelector("[data-map-count]");
    if (n) n.textContent = spots.length + "か所";
  }).catch(() => { box.innerHTML = '<p class="empty">地図を読み込めませんでした。</p>'; });
})();
