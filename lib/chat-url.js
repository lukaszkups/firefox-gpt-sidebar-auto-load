/* Shared URL rules for the sidebar resume add-on.
   Loaded as a classic script in the background page and content scripts.
   Also importable from Node tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    root.ChatUrl = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const HOSTS = new Set(["chatgpt.com", "www.chatgpt.com", "chat.openai.com"]);
  const GENERIC_TITLES = new Set([
    "chatgpt",
    "chat gpt",
    "new chat",
    "chat",
    "home",
  ]);

  function parse(href) {
    try {
      const url = new URL(href);
      if (url.protocol !== "https:" || !HOSTS.has(url.hostname)) {
        return null;
      }
      return url;
    } catch (error) {
      return null;
    }
  }

  function conversationFromUrl(href) {
    const url = parse(href);
    if (!url) {
      return null;
    }
    const parts = url.pathname.split("/").filter(Boolean);
    for (let i = parts.length - 2; i >= 0; i -= 1) {
      if (parts[i] !== "c") {
        continue;
      }
      const id = parts[i + 1];
      if (!/^[A-Za-z0-9_-]{8,}$/.test(id)) {
        continue;
      }
      return {
        id,
        url: url.origin + "/" + parts.slice(0, i + 2).join("/"),
      };
    }
    return null;
  }

  function hasNewChatIntent(url) {
    const params = url.searchParams;
    if (params.has("q") || params.has("prompt") || params.has("hints")) {
      return true;
    }
    if (params.get("temporary-chat") === "true") {
      return true;
    }
    if (url.hash && url.hash !== "#") {
      return true;
    }
    return false;
  }

  function isFreshChatUrl(href) {
    const url = parse(href);
    if (!url || conversationFromUrl(href) || hasNewChatIntent(url)) {
      return false;
    }
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length === 0) {
      return true;
    }
    return parts.length === 1 && (parts[0] === "chat" || parts[0] === "new");
  }

  function cleanTitle(title) {
    if (!title) {
      return "";
    }
    let text = String(title).replace(/\s+/g, " ").trim();
    text = text.replace(/\s+[-|–—]\s+ChatGPT\s*$/i, "").trim();
    if (!text || GENERIC_TITLES.has(text.toLowerCase())) {
      return "";
    }
    return text;
  }

  /**
   * Whether a fresh ChatGPT load should be sent to the saved conversation.
   * Session flags and Firefox prompt injection are handled by the content script.
   */
  function decideRestore(input) {
    if (!input || input.enabled === false) {
      return null;
    }
    if (!input.inSidebar && !input.includeTabs) {
      return null;
    }
    if (!isFreshChatUrl(input.href)) {
      return null;
    }
    const saved = input.lastUrl && conversationFromUrl(input.lastUrl);
    return saved ? saved.url : null;
  }

  return {
    conversationFromUrl,
    isFreshChatUrl,
    cleanTitle,
    decideRestore,
  };
});
