(() => {
  const shell = document.querySelector(".shell");
  if (!shell) return;

  const wsUrl = shell.dataset.wsUrl;
  const detailBaseUrl = shell.dataset.detailBaseUrl;
  const refreshTargets = {
    overview: { url: shell.dataset.overviewUrl, target: "#console-overview" },
    sessions: { url: shell.dataset.sessionsUrl, target: "#console-sessions" },
    jobs: { url: shell.dataset.jobsUrl, target: "#console-jobs" },
    archives: { url: shell.dataset.archivesUrl, target: "#console-archives" },
    evaluations: { url: shell.dataset.evaluationsUrl, target: "#console-evaluations" },
    scenarios: { url: shell.dataset.scenariosUrl, target: "#console-scenarios" },
    entity: { url: shell.dataset.entityUrl, target: "#console-entity" },
  };
  const pending = new Map();
  let socket = null;
  let selectedSession = shell.dataset.selectedSession || "";
  let selectedProjectorName = shell.dataset.selectedProjectorName || "session-runtime";
  let selectedProjectorVersion = shell.dataset.selectedProjectorVersion || "v2";

  function refreshPanel(key) {
    const target = refreshTargets[key];
    if (!target || !window.htmx) {
      return;
    }
    window.htmx.ajax("GET", target.url, {
      target: target.target,
      swap: "innerHTML",
    });
  }

  function refreshDetail() {
    if (!window.htmx) {
      return;
    }
    const params = new URLSearchParams();
    if (selectedSession) {
      params.set("session_id", selectedSession);
    }
    params.set("projector_name", selectedProjectorName);
    params.set("version", selectedProjectorVersion);
    const url = params.size
      ? `${detailBaseUrl}?${params.toString()}`
      : detailBaseUrl;
    window.htmx.ajax("GET", url, {
      target: "#console-session-detail",
      swap: "innerHTML",
    });
  }

  function queueRefresh(kind, callback, delay = 120) {
    if (pending.has(kind)) {
      return;
    }
    pending.set(
      kind,
      window.setTimeout(() => {
        pending.delete(kind);
        callback();
      }, delay),
    );
  }

  function subscribe(streamId, includeBacklog) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }
    socket.send(
      JSON.stringify({
        type: "subscribe",
        stream_id: streamId || null,
        include_backlog: Boolean(includeBacklog),
      }),
    );
  }

  function connect() {
    socket = new WebSocket(wsUrl);
    socket.addEventListener("open", () => {
      subscribe(selectedSession, true);
    });
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "hello") {
        return;
      }
      if (message.type === "trace_batch" || message.type === "session_projection") {
        queueRefresh("detail", refreshDetail);
        queueRefresh("sessions", () => refreshPanel("sessions"));
        queueRefresh("evaluations", () => refreshPanel("evaluations"));
        queueRefresh("scenarios", () => refreshPanel("scenarios"));
        queueRefresh("entity", () => refreshPanel("entity"));
        return;
      }
      if (message.type === "job_update") {
        queueRefresh("overview", () => refreshPanel("overview"));
        queueRefresh("jobs", () => refreshPanel("jobs"));
        queueRefresh("sessions", () => refreshPanel("sessions"));
        queueRefresh("evaluations", () => refreshPanel("evaluations"));
        queueRefresh("scenarios", () => refreshPanel("scenarios"));
        queueRefresh("entity", () => refreshPanel("entity"));
        return;
      }
      if (message.type === "archive_update") {
        queueRefresh("overview", () => refreshPanel("overview"));
        queueRefresh("archives", () => refreshPanel("archives"));
        queueRefresh("sessions", () => refreshPanel("sessions"));
        queueRefresh("scenarios", () => refreshPanel("scenarios"));
        queueRefresh("entity", () => refreshPanel("entity"));
        return;
      }
      if (message.type === "runtime_overview") {
        queueRefresh("overview", () => refreshPanel("overview"));
        queueRefresh("entity", () => refreshPanel("entity"));
      }
    });
    socket.addEventListener("close", () => {
      window.setTimeout(connect, 1000);
    });
  }

  window.relationshipOSConsole = {
    selectSession(sessionId) {
      selectedSession = sessionId || "";
      if (shell) {
        shell.dataset.selectedSession = selectedSession;
      }
      subscribe(selectedSession, false);
      queueRefresh("detail", refreshDetail, 20);
    },
    selectProjector(name, version) {
      selectedProjectorName = name || "session-runtime";
      selectedProjectorVersion = version || shell.dataset.selectedProjectorVersion || "v2";
      if (shell) {
        shell.dataset.selectedProjectorName = selectedProjectorName;
        shell.dataset.selectedProjectorVersion = selectedProjectorVersion;
      }
      queueRefresh("detail", refreshDetail, 20);
    },
  };

  connect();
})();
