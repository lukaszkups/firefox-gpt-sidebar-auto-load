# ChatGPT Sidebar Resume

Firefox’s chatbot sidebar loads `https://chatgpt.com` every time you toggle it on, so ChatGPT starts a new chat and the one you were just in disappears. This add-on sends that sidebar back to the last conversation it had open.

Normal ChatGPT tabs are left alone. While the sidebar stays open, New chat still starts a fresh conversation. The next time you close the sidebar and turn it back on, the conversation you were in is loaded again.

## Install in Firefox

1. Open `about:debugging`.
2. Click **This Firefox**.
3. Click **Load Temporary Add-on**.
4. Choose `manifest.json` in this folder.

Temporary add-ons stay installed until you close Firefox. To keep it permanently, zip this folder and submit it on [addons.mozilla.org](https://addons.mozilla.org/).

The sidebar chatbot itself has to be turned on in Firefox: **Settings → AI Controls → Chatbot in sidebar**, with ChatGPT selected.

## Use it

1. Click the toolbar button if you want to confirm the add-on is on.
2. Open the ChatGPT sidebar and use a conversation (or start one and send a message, so it gets a link).
3. Close the sidebar and open it again. That conversation should be there. The panel may stay blank for a moment while the new-chat page loads, then it switches to the saved conversation.

The button shows the saved title. **Forget saved chat** clears it. **Resume last chat** turns the redirect off without removing the add-on.

If reopening the sidebar still lands on a new chat, open the button menu, expand **Sidebar still starts a new chat?**, and enable resuming in every ChatGPT window. That also changes ordinary tabs that open a new chat.

## What it does not change

- A prompt Firefox sends into the sidebar (for example Summarize page) still starts a new chat when the composer is filled as the page loads.
- Choosing **New chat** inside an already open sidebar is unchanged.
- The add-on only reads the conversation address and page title on ChatGPT. It does not read message text and it does not talk to any server of its own.

## Develop

```bash
node test/chat-url.test.js
```

Icons are regenerated with `python3 scripts/make-icons.py`.
