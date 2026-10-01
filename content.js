const RESTORED_KEY = "chatgptSidebarResume.restored";

function holdPage() {
  document.documentElement.setAttribute("data-sidebar-resume-hold", "");
}

function releasePage() {
  document.documentElement.removeAttribute("data-sidebar-resume-hold");
}

function sessionRestored() {
  try {
    return sessionStorage.getItem(RESTORED_KEY) === "1";
  } catch (error) {
    return false;
  }
}

function markSessionRestored() {
  try {
    sessionStorage.setItem(RESTORED_KEY, "1");
  } catch (error) {
    /* Private browsing can throw if storage is blocked. Restoring still works. */
  }
}

function composerText() {
  const el = document.querySelector("#prompt-textarea");
  if (!el) {
    return null;
  }
  return (el.innerText || el.textContent || "").replace(/\u200b/g, "").trim();
}

/* Firefox delivers sidebar prompts by reloading chatgpt.com and filling
   #prompt-textarea. Placeholder copy that is already in the node does not
   count; only text that shows up after an empty composer does. */
function composerWasPrefilled() {
  const deadline = performance.now() + 1100;
  let sawEmpty = false;
  let emptySince = 0;
  let observer = null;
  let timer = null;
  return new Promise((resolve) => {
    let settled = false;
    const finish = (prefilled) => {
      if (settled) {
        return;
      }
      settled = true;
      observer.disconnect();
      clearInterval(timer);
      resolve(prefilled);
    };
    const inspect = () => {
      const text = composerText();
      if (text === "") {
        if (!sawEmpty) {
          sawEmpty = true;
          emptySince = performance.now();
        } else if (performance.now() - emptySince > 180) {
          finish(false);
        }
      } else if (text && sawEmpty) {
        finish(true);
      }
      if (performance.now() >= deadline) {
        finish(false);
      }
    };
    observer = new MutationObserver(inspect);
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    timer = setInterval(inspect, 30);
    inspect();
  });
}

function watchConversation() {
  let lastKey = "";

  const report = () => {
    const convo = ChatUrl.conversationFromUrl(location.href);
    if (!convo) {
      return;
    }
    const title = ChatUrl.cleanTitle(document.title);
    const key = convo.url + "\n" + title;
    if (key === lastKey) {
      return;
    }
    lastKey = key;
    browser.runtime.sendMessage({
      type: "remember",
      url: convo.url,
      id: convo.id,
      title,
    }).catch(() => {});
  };

  report();
  window.addEventListener("popstate", report);
  if (window.navigation && typeof window.navigation.addEventListener === "function") {
    window.navigation.addEventListener("navigatesuccess", report);
  }
  document.addEventListener("DOMContentLoaded", () => {
    const titleEl = document.querySelector("title");
    if (titleEl) {
      new MutationObserver(report).observe(titleEl, {
        childList: true,
        characterData: true,
        subtree: true,
      });
    }
    report();
  });
  setInterval(report, 1000);
}

async function maybeRestore() {
  if (!ChatUrl.isFreshChatUrl(location.href)) {
    watchConversation();
    return;
  }

  try {
    const decision = await browser.runtime.sendMessage({
      type: "shouldRestore",
      href: location.href,
    });

    // Only hide once we know this is the sidebar (or the all-windows
    // fallback) and a saved conversation is ready. Regular tabs stay visible.
    if (!decision || !decision.redirectTo || sessionRestored()) {
      watchConversation();
      return;
    }

    holdPage();
    const prefilled = await composerWasPrefilled();
    markSessionRestored();
    if (prefilled) {
      releasePage();
      watchConversation();
      return;
    }

    location.replace(decision.redirectTo);
  } catch (error) {
    releasePage();
    watchConversation();
  }
}

maybeRestore();
