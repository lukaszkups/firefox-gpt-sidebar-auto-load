/* The Firefox chatbot sidebar is not a tab. Pages loaded there have no
   sender.tab, which is how this add-on tells the sidebar apart from a
   normal ChatGPT window. */

const state = {
  enabled: true,
  includeTabs: false,
  lastConversation: null,
  lastSidebarSeenAt: null,
};

const ready = browser.storage.local
  .get({
    enabled: true,
    includeTabs: false,
    lastConversation: null,
    lastSidebarSeenAt: null,
  })
  .then((stored) => {
    state.enabled = stored.enabled !== false;
    state.includeTabs = stored.includeTabs === true;
    state.lastConversation = stored.lastConversation;
    state.lastSidebarSeenAt = stored.lastSidebarSeenAt;
  });

browser.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") {
    return;
  }
  if (changes.enabled) {
    state.enabled = changes.enabled.newValue !== false;
  }
  if (changes.includeTabs) {
    state.includeTabs = changes.includeTabs.newValue === true;
  }
  if (Object.prototype.hasOwnProperty.call(changes, "lastConversation")) {
    state.lastConversation = changes.lastConversation.newValue || null;
  }
  if (Object.prototype.hasOwnProperty.call(changes, "lastSidebarSeenAt")) {
    state.lastSidebarSeenAt = changes.lastSidebarSeenAt.newValue || null;
  }
});

function touchSidebar() {
  const now = Date.now();
  if (state.lastSidebarSeenAt && now - state.lastSidebarSeenAt < 60 * 1000) {
    state.lastSidebarSeenAt = now;
    return;
  }
  state.lastSidebarSeenAt = now;
  browser.storage.local.set({ lastSidebarSeenAt: now });
}

function handle(message, sender) {
  const inSidebar = !sender.tab;

  if (message.type === "shouldRestore") {
    if (inSidebar) {
      touchSidebar();
    }
    const redirectTo = ChatUrl.decideRestore({
      enabled: state.enabled,
      includeTabs: state.includeTabs,
      inSidebar,
      href: message.href,
      lastUrl: state.lastConversation && state.lastConversation.url,
    });
    return { redirectTo, inSidebar };
  }

  if (message.type === "remember") {
    if (!inSidebar && !state.includeTabs) {
      return { ok: false, inSidebar };
    }
    if (inSidebar) {
      touchSidebar();
    }
    const convo = ChatUrl.conversationFromUrl(message.url);
    if (!convo) {
      return { ok: false };
    }
    const title = ChatUrl.cleanTitle(message.title || "");
    const prev = state.lastConversation;
    if (prev && prev.url === convo.url && (prev.title || "") === title) {
      return { ok: true, unchanged: true };
    }
    const lastConversation = {
      url: convo.url,
      id: convo.id,
      title,
      savedAt: Date.now(),
    };
    state.lastConversation = lastConversation;
    return browser.storage.local.set({ lastConversation }).then(() => ({ ok: true }));
  }

  if (message.type === "getStatus") {
    return {
      enabled: state.enabled,
      includeTabs: state.includeTabs,
      lastConversation: state.lastConversation,
      lastSidebarSeenAt: state.lastSidebarSeenAt,
    };
  }

  return undefined;
}

browser.runtime.onMessage.addListener((message, sender) => {
  return ready.then(() => handle(message, sender));
});
