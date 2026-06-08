let pollTimer = null;
let inspectorDir = null;
let inspectorDuration = 0;
let inspectorCueIndex = -1;
let inspectorReq = 0;
let projectDuration = 0;

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

function log(lines) {
  const el = document.getElementById("log-output");
  el.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines);
}

function badge(name, ok) {
  const s = document.createElement("span");
  s.className = "badge " + (ok ? "ok" : "miss");
  s.textContent = name;
  return s;
}

async function loadProject() {
  const data = await api("/api/project");
  const m = data.manifest || {};
  document.getElementById("project-meta").textContent =
    `${m.megapost_slug || "project"} · post ${m.post_id || "?"} · ${(data.status?.segments || []).length} segments`;
  const mt = data.merge_transitions || { default: "crossfade", duration_sec: 0.3 };
  document.getElementById("transition-type").value = mt.default || "crossfade";
  document.getElementById("transition-dur").value = mt.duration_sec ?? 0.3;
  const fv = data.status?.final_video;
  const vid = document.getElementById("final-video");
  const scrub = document.getElementById("final-scrubber");
  const atEl = document.getElementById("final-at");
  if (fv) {
    vid.src = "/assets/" + fv.path + "?t=" + Date.now();
    document.getElementById("final-dur").textContent = fv.duration_sec + "s";
    try {
      const pt = await api("/api/project/timeline");
      projectDuration = pt.total_duration_sec || fv.duration_sec || 1;
      scrub.max = projectDuration;
      scrub.classList.remove("hidden");
      atEl.classList.remove("hidden");
    } catch (e) {
      projectDuration = fv.duration_sec || 1;
    }
  }
}

function segmentCard(seg) {
  const card = document.createElement("article");
  card.className = "card";
  const h = document.createElement("h3");
  h.textContent = seg.title || seg.dir;
  card.appendChild(h);

  const badges = document.createElement("div");
  badges.className = "badges";
  Object.entries(seg.checks || {}).forEach(([k, v]) => badges.appendChild(badge(k, v)));
  card.appendChild(badges);

  if (seg.thumbnail) {
    const img = document.createElement("img");
    img.className = "thumb";
    img.src = seg.thumbnail + "?t=" + Date.now();
    card.appendChild(img);
  }

  const ta = document.createElement("textarea");
  ta.className = "script";
  ta.dataset.dir = seg.dir;
  ta.value = seg.script || "";
  card.appendChild(ta);

  const saveBtn = document.createElement("button");
  saveBtn.className = "secondary";
  saveBtn.textContent = "Save script";
  saveBtn.onclick = async () => {
    try {
      await api(`/api/segments/${encodeURIComponent(seg.dir)}/script`, {
        method: "PATCH",
        body: JSON.stringify({ text: ta.value }),
      });
      log(`Saved script: ${seg.dir}`);
    } catch (e) {
      log(`Error: ${e.message}`);
    }
  };
  card.appendChild(saveBtn);

  if (seg.preview) {
    const v = document.createElement("video");
    v.controls = true;
    v.dataset.preview = seg.preview;
    v.src = seg.preview + "?t=" + Date.now();
    card.appendChild(v);
  }

  const actions = document.createElement("div");
  actions.className = "actions";
  [
    ["Regenerate script", "script"],
    ["Regenerate audio", "audio"],
    ["Regenerate heroes", "hero"],
    ["Rebuild deck", "deck"],
    ["Regenerate segment", "full_segment"],
  ].forEach(([label, change]) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.onclick = () => runRegenerate(change, seg.dir);
    actions.appendChild(b);
  });
  const inspectBtn = document.createElement("button");
  inspectBtn.className = "inspect-btn secondary";
  inspectBtn.textContent = "Timeline inspector";
  inspectBtn.onclick = () => openInspector(seg.dir, seg.preview);
  card.appendChild(inspectBtn);

  card.appendChild(actions);
  return card;
}

async function updateInspectorAt(t) {
  if (!inspectorDir) return;
  const req = ++inspectorReq;
  try {
    const data = await api(`/api/segments/${encodeURIComponent(inspectorDir)}/at?t=${t}`);
    if (req !== inspectorReq) return;
    const frame = document.getElementById("inspector-frame");
    const slide = data.slide || {};
    const url =
      (slide.frame_urls && (slide.frame_urls.mid || slide.frame_urls.start)) ||
      slide.jpeg_url;
    if (url) frame.src = url + "?t=" + Date.now();
    else frame.removeAttribute("src");
    document.getElementById("inspector-caption").textContent =
      data.caption ? data.caption.text : (slide.notes || "");
    const w = data.word;
    const wordEl = document.getElementById("inspector-word");
    if (w && (slide.words || []).length) {
      wordEl.innerHTML = (slide.words || [])
        .map((x, i) =>
          `<span class="${i === w.index ? "karaoke-active" : ""}">${x.word}</span>`
        )
        .join(" ");
    } else {
      wordEl.textContent = w
        ? `Word: ${w.active} · window: ${(w.window || []).join(" ")}`
        : "Word-level: cue only (run transcribe with words for karaoke)";
    }
    const idx = data.slide_index ?? -1;
    if (idx !== inspectorCueIndex) {
      inspectorCueIndex = idx;
      document.querySelectorAll("#inspector-slides img").forEach((img, i) => {
        img.classList.toggle("active", i === idx);
      });
    }
  } catch (e) {
    document.getElementById("inspector-caption").textContent = `Inspector error: ${e.message}`;
  }
}

async function updateProjectAt(t) {
  try {
    const data = await api(`/api/project/at?t=${t}`);
    const el = document.getElementById("final-at");
    const slide = data.slide || {};
    const seg = data.segment_dir || "";
    el.textContent = `${seg} @ ${t.toFixed(1)}s — ${data.caption?.text || slide.notes || ""}`;
  } catch (_) {
    document.getElementById("final-at").textContent = "";
  }
}

async function openInspector(dir, preview) {
  try {
    inspectorDir = dir;
    document.getElementById("inspector").classList.remove("hidden");
    document.getElementById("inspector-title").textContent = dir;
    const tl = await api(`/api/segments/${encodeURIComponent(dir)}/timeline`);
    inspectorDuration = tl.duration_sec || 1;
    const scrub = document.getElementById("inspector-scrubber");
    scrub.max = inspectorDuration;
    scrub.value = 0;
    const vid = document.getElementById("inspector-video");
    if (preview) vid.src = preview + "?t=" + Date.now();
    const strip = document.getElementById("inspector-slides");
    strip.innerHTML = "";
    (tl.cues || []).forEach((c) => {
      const img = document.createElement("img");
      const thumb =
        (c.frame_urls && (c.frame_urls.start || c.frame_urls.mid)) || c.jpeg_url || "";
      img.src = thumb + "?t=" + Date.now();
      img.title = c.notes || "";
      img.onclick = () => {
        scrub.value = c.start_sec;
        vid.currentTime = c.start_sec;
        updateInspectorAt(c.start_sec);
      };
      strip.appendChild(img);
    });
    try {
      const sync = await api(`/api/segments/${encodeURIComponent(dir)}/sync-check`);
      const el = document.getElementById("inspector-sync");
      el.textContent = sync.ok ? "Sync OK" : "Sync issues: " + (sync.issues || []).join("; ");
      el.className = "sync-badge" + (sync.ok ? "" : " fail");
    } catch (e) {
      const el = document.getElementById("inspector-sync");
      el.textContent = "Sync check failed: " + e.message;
      el.className = "sync-badge fail";
    }
    scrub.oninput = () => {
      const t = parseFloat(scrub.value);
      if (Math.abs(vid.currentTime - t) > 0.15) vid.currentTime = t;
      updateInspectorAt(t);
    };
    vid.onseeked = () => {
      scrub.value = vid.currentTime;
      updateInspectorAt(vid.currentTime);
    };
    vid.ontimeupdate = () => {
      scrub.value = vid.currentTime;
      updateInspectorAt(vid.currentTime);
    };
    updateInspectorAt(0);
  } catch (e) {
    log(`Inspector error (${dir}): ${e.message}`);
  }
}

async function loadSegments() {
  const data = await api("/api/segments");
  const grid = document.getElementById("segments-grid");
  grid.innerHTML = "";
  (data.segments || []).forEach((seg) => grid.appendChild(segmentCard(seg)));
}

function pollJob(jobId) {
  if (pollTimer) clearInterval(pollTimer);
  const tick = async () => {
    try {
      const job = await api(`/api/jobs/${jobId}`);
      if (job.error) {
        log(`Job ${jobId} not found`);
        clearInterval(pollTimer);
        pollTimer = null;
        return;
      }
      log(job.log || []);
      if (job.status === "done" || job.status === "error") {
        clearInterval(pollTimer);
        pollTimer = null;
        await loadProject();
        await loadSegments();
      }
    } catch (e) {
      log(`Poll error: ${e.message}`);
    }
  };
  tick();
  pollTimer = setInterval(tick, 1200);
}

async function runStage(stage, segments, force = true) {
  try {
    log(`Starting ${stage}…`);
    const job = await api("/api/run", {
      method: "POST",
      body: JSON.stringify({ stage, segments, force }),
    });
    if (job.log?.length) log(job.log);
    if (job.id) pollJob(job.id);
  } catch (e) {
    log(`Error: ${e.message}`);
  }
}

async function runRegenerate(change, segment) {
  try {
    log(`Regenerate ${change} for ${segment}…`);
    const job = await api("/api/regenerate", {
      method: "POST",
      body: JSON.stringify({ change, segment, force: true }),
    });
    if (job.log?.length) log(job.log);
    if (job.id) pollJob(job.id);
  } catch (e) {
    log(`Error: ${e.message}`);
  }
}

document.getElementById("btn-save-transitions").onclick = async () => {
  try {
    const dur = parseFloat(document.getElementById("transition-dur").value);
    await api("/api/protocol/merge-transitions", {
      method: "POST",
      body: JSON.stringify({
        default: document.getElementById("transition-type").value,
        duration_sec: dur,
      }),
    });
    log("Saved merge transition settings.");
  } catch (e) {
    log(`Error: ${e.message}`);
  }
};

document.getElementById("btn-remerge").onclick = () => runStage("merge", null, false);
document.getElementById("btn-publish").onclick = () => runStage("publish", null, false);

const finalVid = document.getElementById("final-video");
const finalScrub = document.getElementById("final-scrubber");
finalScrub.oninput = () => {
  const t = parseFloat(finalScrub.value);
  if (Math.abs(finalVid.currentTime - t) > 0.15) finalVid.currentTime = t;
  updateProjectAt(t);
};
finalVid.onseeked = () => {
  finalScrub.value = finalVid.currentTime;
  updateProjectAt(finalVid.currentTime);
};
finalVid.ontimeupdate = () => {
  finalScrub.value = finalVid.currentTime;
  updateProjectAt(finalVid.currentTime);
};

(async () => {
  await loadProject();
  await loadSegments();
})();
