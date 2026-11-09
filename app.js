(function () {
  "use strict";

  var library = window.VIDEO_LIBRARY;
  var refs = {
    directory: document.getElementById("chapter-directory"),
    fallback: document.getElementById("directory-fallback"),
    stats: document.getElementById("directory-stats"),
    video: document.getElementById("video-player"),
    playerFrame: document.getElementById("player-frame"),
    idle: document.getElementById("player-idle"),
    playFirst: document.getElementById("play-first"),
    loading: document.getElementById("player-loading"),
    chapter: document.getElementById("current-chapter"),
    heading: document.getElementById("player-heading"),
    original: document.getElementById("player-original"),
    status: document.getElementById("player-status")
  };
  var currentId = null;
  var currentButton = null;
  var selectionToken = 0;

  function text(value) {
    return value === null || value === undefined ? "" : String(value);
  }

  function formatDuration(totalSeconds) {
    var seconds = Number(totalSeconds);
    if (!Number.isFinite(seconds) || seconds < 0) return "—";
    seconds = Math.round(seconds);
    var hours = Math.floor(seconds / 3600);
    var minutes = Math.floor((seconds % 3600) / 60);
    var remainder = seconds % 60;
    if (hours > 0) return hours + ":" + String(minutes).padStart(2, "0") + ":" + String(remainder).padStart(2, "0");
    return minutes + ":" + String(remainder).padStart(2, "0");
  }

  function setStatus(message, kind) {
    refs.status.textContent = text(message);
    refs.status.classList.toggle("is-error", kind === "error");
  }

  function chapterLabel(chapter) {
    if (!chapter) return "";
    if (library.directoryMode === "flat") return text(chapter.title);
    var number = chapter.number === null || chapter.number === undefined ? "补充" : "第 " + chapter.number + " 章";
    return number + " · " + text(chapter.title);
  }

  function buildStats() {
    var chapters = Array.isArray(library.chapters) ? library.chapters.filter(function (chapter) {
      return chapter && chapter.number !== null && chapter.number !== undefined;
    }).length : 0;
    var total = Number(library.totalVideos);
    var duration = formatDuration(library.totalDuration);
    var strong = document.createElement("strong");
    strong.textContent = Number.isFinite(total) ? String(total).padStart(2, "0") : "—";
    var label = document.createElement("span");
    label.textContent = library.directoryMode === "flat" ? "段视频 · " + duration : chapters + " chapters · " + duration;
    refs.stats.replaceChildren(strong, label);
  }

  function makeVideoButton(video, chapter) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "video-entry";
    button.dataset.videoId = text(video.id);
    button.setAttribute("aria-label", text(video.number ? video.number + " " : "") + text(video.title) + "，时长 " + formatDuration(video.duration));

    var index = document.createElement("span");
    index.className = "video-index";
    index.textContent = video.number ? text(video.number) : "—";
    var copy = document.createElement("span");
    copy.className = "video-copy";
    var title = document.createElement("span");
    title.className = "video-title";
    title.textContent = text(video.title);
    copy.appendChild(title);
    var duration = document.createElement("span");
    duration.className = "video-duration";
    duration.textContent = formatDuration(video.duration);
    button.append(index, copy, duration);
    button.addEventListener("click", function () {
      selectVideo(video, chapter, button);
    });
    return button;
  }

  function buildDirectory() {
    refs.directory.replaceChildren();
    var chapters = Array.isArray(library.chapters) ? library.chapters : [];
    var firstChapter = true;
    var firstVideo = null;
    chapters.forEach(function (chapter) {
      var details = document.createElement("details");
      details.className = "chapter";
      if (firstChapter) details.open = true;
      firstChapter = false;
      var summary = document.createElement("summary");
      var summaryInner = document.createElement("span");
      summaryInner.className = "chapter-summary";
      var number = document.createElement("span");
      number.className = "chapter-number";
      number.textContent = chapter.number === null || chapter.number === undefined ? "＋" : String(chapter.number).padStart(2, "0");
      var chapterTitle = document.createElement("span");
      chapterTitle.className = "chapter-title";
      chapterTitle.appendChild(document.createTextNode(text(chapter.title)));
      if (chapter.englishTitle) {
        var english = document.createElement("small");
        english.textContent = text(chapter.englishTitle);
        chapterTitle.appendChild(english);
      }
      var chevron = document.createElement("span");
      chevron.className = "chapter-chevron";
      chevron.setAttribute("aria-hidden", "true");
      summaryInner.append(number, chapterTitle, chevron);
      summary.appendChild(summaryInner);
      details.appendChild(summary);

      var list = document.createElement("ol");
      list.className = "video-list";
      var videos = Array.isArray(chapter.videos) ? chapter.videos : [];
      videos.forEach(function (video) {
        var item = document.createElement("li");
        var button = makeVideoButton(video, chapter);
        item.appendChild(button);
        list.appendChild(item);
        if (!firstVideo) firstVideo = { video: video, chapter: chapter, button: button };
      });
      if (library.directoryMode === "flat") {
        list.classList.add("video-list-flat");
        refs.directory.appendChild(list);
      } else {
        details.appendChild(list);
        refs.directory.appendChild(details);
      }
    });
    if (!firstVideo) {
      var empty = document.createElement("p");
      empty.className = "directory-fallback";
      empty.textContent = "暂时没有可播放的视频。";
      refs.directory.appendChild(empty);
    }
    refs.playFirst.addEventListener("click", function () {
      if (firstVideo) selectVideo(firstVideo.video, firstVideo.chapter, firstVideo.button);
    });
  }

  function markCurrent(button) {
    if (currentButton) {
      currentButton.classList.remove("is-current");
      currentButton.removeAttribute("aria-current");
    }
    currentButton = button || null;
    if (currentButton) {
      currentButton.classList.add("is-current");
      currentButton.setAttribute("aria-current", "true");
    }
  }

  function showPlayerMessage(message, kind) {
    setStatus(message, kind);
    refs.loading.classList.remove("is-visible");
  }

  function selectVideo(video, chapter, button) {
    if (!video || !video.src) {
      showPlayerMessage("这段视频暂时没有可用文件。", "error");
      return;
    }
    currentId = text(video.id);
    selectionToken += 1;
    var activeToken = selectionToken;
    markCurrent(button);
    refs.idle.classList.add("is-hidden");
    refs.chapter.textContent = chapterLabel(chapter);
    refs.heading.textContent = text(video.title) || "未命名视频";
    var displayNumber = video.number ? "编号 " + text(video.number) : "补充视频";
    refs.original.textContent = displayNumber + " · 时长 " + formatDuration(video.duration);
    refs.video.setAttribute("aria-label", text(video.title) + "，视频播放器");
    refs.loading.classList.add("is-visible");
    setStatus("正在载入 · " + formatDuration(video.duration), "loading");

    refs.video.pause();
    refs.video.src = text(video.src);
    refs.video.load();

    var playAttempt = refs.video.play();
    if (playAttempt && typeof playAttempt.then === "function") {
      playAttempt.then(function () {
        if (activeToken !== selectionToken) return;
        showPlayerMessage("播放中 · " + formatDuration(video.duration));
      }).catch(function (error) {
        if (activeToken !== selectionToken) return;
        if (error && error.name === "NotAllowedError") {
          showPlayerMessage("已载入，请按播放器中的播放键开始。", "info");
          return;
        }
        showPlayerMessage("视频暂时无法播放，请使用播放器按钮重试。", "error");
      });
    }

    if (window.matchMedia && window.matchMedia("(max-width: 900px)").matches && refs.playerFrame.scrollIntoView) {
      window.setTimeout(function () {
        refs.playerFrame.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    }
  }

  function bindMediaEvents() {
    refs.video.addEventListener("loadstart", function () { refs.loading.classList.add("is-visible"); });
    refs.video.addEventListener("canplay", function () { refs.loading.classList.remove("is-visible"); });
    refs.video.addEventListener("playing", function () { refs.loading.classList.remove("is-visible"); setStatus("播放中"); });
    refs.video.addEventListener("pause", function () {
      if (!refs.video.ended && currentId && !refs.video.error && refs.video.readyState !== 0 && !refs.status.classList.contains("is-error")) {
        setStatus("已暂停 · 按播放键继续");
      }
    });
    refs.video.addEventListener("waiting", function () {
      if (refs.video.error || refs.status.classList.contains("is-error")) return;
      refs.loading.classList.add("is-visible");
      setStatus("正在缓冲…");
    });
    refs.video.addEventListener("ended", function () { refs.loading.classList.remove("is-visible"); setStatus("播放结束 · 可重新播放"); });
    refs.video.addEventListener("error", function () {
      var mediaError = refs.video.error;
      refs.loading.classList.remove("is-visible");
      if (!currentId) return;
      var detail = mediaError && mediaError.code === 4 ? "视频无法加载，或浏览器不支持此格式。" : "视频暂时无法加载，请稍后重试。";
      setStatus(detail, "error");
    });
  }

  function showCatalogError() {
    refs.fallback.textContent = "视频目录暂时无法加载，请刷新页面重试。";
    refs.stats.textContent = "目录不可用";
    setStatus("目录尚未准备好。", "error");
  }

  if (!library || !Array.isArray(library.chapters)) {
    showCatalogError();
    return;
  }
  buildStats();
  buildDirectory();
  bindMediaEvents();
})();
