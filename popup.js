const enabledButton = document.getElementById("enabled");
const includeTabs = document.getElementById("include-tabs");
const titleEl = document.getElementById("title");
const metaEl = document.getElementById("meta");
const noticeEl = document.getElementById("notice");
const clearButton = document.getElementById("clear");

function formatSaved(timestamp) {
  if (!timestamp) {
    return "";
  }
  const minutes = Math.round((Date.now() - timestamp) / 60000);
  if (minutes < 1) {
    return "Saved just now";
  }
  if (minutes < 60) {
    return minutes === 1 ? "Saved 1 minute ago" : `Saved ${minutes} minutes ago`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 36) {
    return hours === 1 ? "Saved 1 hour ago" : `Saved ${hours} hours ago`;
  }
  const days = Math.round(hours / 24);
  return days === 1 ? "Saved 1 day ago" : `Saved ${days} days ago`;
}

function render(status) {
  const on = status.enabled !== false;
  enabledButton.setAttribute("aria-checked", on ? "true" : "false");
  includeTabs.checked = status.includeTabs === true;

  const convo = status.lastConversation;
  if (convo && convo.url) {
    titleEl.textContent = convo.title || "Untitled conversation";
    metaEl.textContent = formatSaved(convo.savedAt);
    clearButton.disabled = false;
  } else {
    titleEl.textContent = "None saved yet";
    metaEl.textContent = "Open a chat in the sidebar and this will fill in.";
    clearButton.disabled = true;
  }

  if (!status.lastSidebarSeenAt) {
    noticeEl.textContent =
      "Waiting for ChatGPT in the Firefox sidebar. Open the sidebar once, send a message, then close and reopen it.";
  } else if (!on) {
    noticeEl.textContent = "Resume is off. The sidebar will keep starting a new chat.";
  } else if (!convo) {
    noticeEl.textContent = "The sidebar was seen, but no conversation has been saved yet.";
  } else {
    noticeEl.textContent = "Next time you open the sidebar, this conversation loads.";
  }
}

function load() {
  return browser.runtime
    .sendMessage({ type: "getStatus" })
    .then(render)
    .catch(() => {
      noticeEl.textContent =
        "Could not reach the add-on. Remove it in about:debugging and load it again.";
    });
}

enabledButton.addEventListener("click", () => {
  const next = enabledButton.getAttribute("aria-checked") !== "true";
  browser.storage.local.set({ enabled: next }).then(load);
});

includeTabs.addEventListener("change", () => {
  browser.storage.local.set({ includeTabs: includeTabs.checked }).then(load);
});

clearButton.addEventListener("click", () => {
  browser.storage.local.set({ lastConversation: null }).then(load);
});

browser.storage.onChanged.addListener(() => {
  load();
});

load();
