# ChatGPT Sidebar Resume

Firefox’s chatbot sidebar loads `https://chatgpt.com` every time you toggle it on, so ChatGPT starts a new chat and the one you were just in disappears. This add-on sends that sidebar back to the last conversation it had open.

Normal ChatGPT tabs are left alone. While the sidebar stays open, New chat still starts a fresh conversation. The next time you close the sidebar and turn it back on, the conversation you were in is loaded again.

## Install it so it stays

Quit Firefox, then from this folder run:

```bash
python3 scripts/install.py
```

On Windows:

```bat
py scripts/install.py
```

That builds `dist/chatgpt-sidebar-resume-1.0.1.xpi` and copies it into your Firefox profile, the same place Firefox keeps other add-ons. It is not a temporary add-on: it is still there after you quit.

Start Firefox and check `about:addons`. If the add-on is listed as disabled, enable it.

The sidebar chatbot also has to be turned on: **Settings → AI Controls → Chatbot in sidebar**, with ChatGPT selected.

### Regular Firefox

The usual Firefox release only runs add-ons Mozilla has signed, so it will refuse this copy. Developer Edition, Nightly, and ESR will run it. The installer turns the signature check off in your profile, which those editions honor.

To use it in regular Firefox, sign your own copy (this does not publish it):

1. Submit the `.xpi` from `dist/` at [addons.mozilla.org/developers](https://addons.mozilla.org/developers/) and choose **On your own**.
2. Download the signed file Mozilla gives back.
3. In Firefox, open `about:addons`, open the gear menu, and choose **Install Add-on From File**.

That install stays after Firefox quits. To remove the sideloaded copy, run `python3 scripts/install.py --remove`.

Loading `manifest.json` from `about:debugging` still works, and Firefox drops that copy when it quits. Use the installer above when you want it to remain.

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
python3 test/install_test.py
```

Icons are regenerated with `python3 scripts/make-icons.py`.
