const assert = require("node:assert/strict");
const { conversationFromUrl, isFreshChatUrl, cleanTitle, decideRestore } = require("../lib/chat-url");

const id = "678eaadd-3bc8-8013-9f15-7b42d34320a4";
const convo = `https://chatgpt.com/c/${id}`;

assert.deepEqual(conversationFromUrl(convo), { id, url: convo });
assert.equal(
  conversationFromUrl(`https://chatgpt.com/g/g-p-project/c/${id}?model=gpt-5`).url,
  `https://chatgpt.com/g/g-p-project/c/${id}`
);
assert.equal(conversationFromUrl("https://chatgpt.com/share/" + id), null);
assert.equal(conversationFromUrl("https://example.com/c/" + id), null);
assert.equal(conversationFromUrl("https://chatgpt.com/c/short"), null);

assert.equal(isFreshChatUrl("https://chatgpt.com/"), true);
assert.equal(isFreshChatUrl("https://chatgpt.com"), true);
assert.equal(isFreshChatUrl("https://chatgpt.com/?model=gpt-5"), true);
assert.equal(isFreshChatUrl("https://chat.openai.com/new"), true);
assert.equal(isFreshChatUrl("https://chatgpt.com/?q=Why+do+birds+fly"), false);
assert.equal(isFreshChatUrl("https://chatgpt.com/?temporary-chat=true"), false);
assert.equal(isFreshChatUrl("https://chatgpt.com/#settings"), false);
assert.equal(isFreshChatUrl(convo), false);
assert.equal(isFreshChatUrl("https://chatgpt.com/auth/login"), false);

assert.equal(cleanTitle("Packing list - ChatGPT"), "Packing list");
assert.equal(cleanTitle("ChatGPT"), "");
assert.equal(cleanTitle("New chat"), "");
assert.equal(cleanTitle("  Trip   plan  "), "Trip plan");

const base = {
  enabled: true,
  includeTabs: false,
  inSidebar: true,
  href: "https://chatgpt.com/",
  lastUrl: convo,
};

assert.equal(decideRestore(base), convo);
assert.equal(decideRestore({ ...base, enabled: false }), null);
assert.equal(decideRestore({ ...base, inSidebar: false }), null);
assert.equal(decideRestore({ ...base, inSidebar: false, includeTabs: true }), convo);
assert.equal(decideRestore({ ...base, href: "https://chatgpt.com/?q=summarize" }), null);
assert.equal(decideRestore({ ...base, lastUrl: null }), null);
assert.equal(decideRestore({ ...base, href: convo }), null);

console.log("chat-url tests passed");
