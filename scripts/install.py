#!/usr/bin/env python3
"""Install ChatGPT Sidebar Resume into Firefox so it survives restart.

Temporary add-ons loaded from about:debugging are deleted when Firefox
quits. This copies a normal .xpi into each Firefox profile and turns on
the preferences those profiles need to keep an unsigned personal add-on.
"""

import argparse
import configparser
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ADDON_ID = "chatgpt-sidebar-resume@example.com"
USERJS_BEGIN = "// BEGIN chatgpt-sidebar-resume"
USERJS_END = "// END chatgpt-sidebar-resume"
USERJS_BLOCK = """{begin}
user_pref("xpinstall.signatures.required", false);
user_pref("extensions.langpacks.signatures.required", false);
user_pref("extensions.autoDisableScopes", 0);
user_pref("extensions.enabledScopes", 15);
{end}
""".format(begin=USERJS_BEGIN, end=USERJS_END)

PACKAGED = (
    "manifest.json",
    "background.js",
    "content.js",
    "content.css",
    "popup.html",
    "popup.css",
    "popup.js",
    "lib/chat-url.js",
    "icons/icon-32.png",
    "icons/icon-48.png",
    "icons/icon-96.png",
)

# Release and Beta ignore xpinstall.signatures.required. These editions honor it.
UNSIGNED_OK = {"nightly", "aurora", "esr", "default", "unbranded"}
CHANNEL_RE = re.compile(r"""app\.update\.channel["']?\s*,\s*["']([a-zA-Z0-9_-]+)["']""")


def repo_root():
    return Path(__file__).resolve().parents[1]


def read_version(root):
    manifest = (root / "manifest.json").read_text(encoding="utf-8")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', manifest)
    if not match:
        raise SystemExit("manifest.json has no version")
    return match.group(1)


def build_xpi(root, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    missing = [name for name in PACKAGED if not (root / name).is_file()]
    if missing:
        raise SystemExit("missing extension files: " + ", ".join(missing))
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in PACKAGED:
            archive.write(root / name, name)
    return destination


def firefox_config_dirs():
    home = Path.home()
    found = []
    candidates = [
        home / ".mozilla" / "firefox",
        home / "snap" / "firefox" / "common" / ".mozilla" / "firefox",
        home / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",
        home / "Library" / "Application Support" / "Firefox",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Mozilla" / "Firefox")
    for path in candidates:
        if (path / "profiles.ini").is_file():
            found.append(path)
    return found


def parse_profiles(config_dir):
    parser = configparser.RawConfigParser()
    parser.read(config_dir / "profiles.ini", encoding="utf-8")
    profiles = {}
    install_paths = []
    for section in parser.sections():
        if section.startswith("Profile"):
            name = parser.get(section, "Path", fallback="").strip()
            if not name:
                continue
            relative = parser.get(section, "IsRelative", fallback="1").strip() != "0"
            path = (config_dir / name).resolve() if relative else Path(name).expanduser().resolve()
            profiles[name] = path
            if parser.get(section, "Default", fallback="0").strip() == "1":
                install_paths.append(path)
        elif section.startswith("Install"):
            name = parser.get(section, "Default", fallback="").strip()
            if name:
                install_paths.append(name)
    chosen = []
    for item in install_paths:
        path = item if isinstance(item, Path) else profiles.get(item)
        if path is None:
            relative = (config_dir / item).resolve()
            path = relative if relative.is_dir() else Path(item).expanduser().resolve()
        if path not in chosen:
            chosen.append(path)
    if not chosen:
        chosen = list(profiles.values())
    return [path for path in chosen if path.is_dir()]


def parse_channel(text):
    match = CHANNEL_RE.search(text)
    return match.group(1).lower() if match else None


def read_channel(app_dir):
    if not app_dir:
        return None
    app_dir = Path(app_dir)
    candidates = [
        app_dir / "defaults" / "pref" / "channel-prefs.js",
        app_dir / "browser" / "defaults" / "preferences" / "channel-prefs.js",
        app_dir.parent / "Resources" / "defaults" / "pref" / "channel-prefs.js",
    ]
    for path in candidates:
        if path.is_file():
            return parse_channel(path.read_text(encoding="utf-8", errors="replace"))
    omni = app_dir / "omni.ja"
    if omni.is_file():
        try:
            with zipfile.ZipFile(omni) as archive:
                for name in (
                    "defaults/pref/channel-prefs.js",
                    "browser/defaults/preferences/channel-prefs.js",
                ):
                    try:
                        return parse_channel(archive.read(name).decode("utf-8", "replace"))
                    except KeyError:
                        continue
        except zipfile.BadZipFile:
            return None
    return None


def profile_channel(profile):
    compat = profile / "compatibility.ini"
    if not compat.is_file():
        return None
    parser = configparser.RawConfigParser()
    parser.read(compat, encoding="utf-8")
    if not parser.has_section("Compatibility"):
        return None
    for key in ("LastAppDir", "LastPlatformDir"):
        app_dir = parser.get("Compatibility", key, fallback="").strip()
        channel = read_channel(app_dir) if app_dir else None
        if channel:
            return channel
    return None


def upsert_user_js(profile):
    path = profile / "user.js"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    pattern = re.compile(
        re.escape(USERJS_BEGIN) + r".*?" + re.escape(USERJS_END) + r"\n?",
        re.DOTALL,
    )
    stripped = pattern.sub("", existing).rstrip()
    text = (stripped + "\n\n" + USERJS_BLOCK).lstrip("\n") if stripped else USERJS_BLOCK
    path.write_text(text, encoding="utf-8")


def remove_user_js_block(profile):
    path = profile / "user.js"
    if not path.is_file():
        return False
    pattern = re.compile(
        r"\n?" + re.escape(USERJS_BEGIN) + r".*?" + re.escape(USERJS_END) + r"\n?",
        re.DOTALL,
    )
    text = pattern.sub("\n", path.read_text(encoding="utf-8")).strip()
    if text:
        path.write_text(text + "\n", encoding="utf-8")
    else:
        path.unlink()
    return True


def firefox_is_running():
    names = ("firefox", "firefox-bin", "firefox-esr")
    if os.name == "nt":
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq firefox.exe"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return False
        return "firefox.exe" in output.lower()
    for name in names:
        try:
            found = subprocess.call(
                ["pgrep", "-x", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return False
        if found == 0:
            return True
    return False


def install_into(profile, xpi):
    extensions = profile / "extensions"
    extensions.mkdir(exist_ok=True)
    target = extensions / (ADDON_ID + ".xpi")
    target.write_bytes(xpi.read_bytes())
    upsert_user_js(profile)
    return target


def remove_from(profile):
    target = profile / "extensions" / (ADDON_ID + ".xpi")
    removed = False
    if target.is_file():
        target.unlink()
        removed = True
    if remove_user_js_block(profile):
        removed = True
    return removed


def iter_profiles(all_profiles):
    found = []
    for config_dir in firefox_config_dirs():
        if all_profiles:
            parser = configparser.RawConfigParser()
            parser.read(config_dir / "profiles.ini", encoding="utf-8")
            paths = []
            for section in parser.sections():
                if not section.startswith("Profile"):
                    continue
                name = parser.get(section, "Path", fallback="").strip()
                if not name:
                    continue
                relative = parser.get(section, "IsRelative", fallback="1").strip() != "0"
                path = (config_dir / name).resolve() if relative else Path(name).expanduser().resolve()
                if path.is_dir():
                    paths.append(path)
            found.extend(paths)
        else:
            found.extend(parse_profiles(config_dir))
    unique = []
    for path in found:
        if path not in unique:
            unique.append(path)
    return unique


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="install into every Firefox profile")
    parser.add_argument("--remove", action="store_true", help="remove the add-on from Firefox profiles")
    parser.add_argument("--xpi-only", action="store_true", help="only build dist/*.xpi")
    args = parser.parse_args(argv)

    root = repo_root()
    version = read_version(root)
    xpi = build_xpi(root, root / "dist" / ("chatgpt-sidebar-resume-" + version + ".xpi"))
    print("Built " + str(xpi))
    if args.xpi_only:
        return 0

    profiles = iter_profiles(args.all)
    if not profiles:
        print("No Firefox profile found. The .xpi above is what you install from about:addons.")
        return 1

    running = firefox_is_running()
    signed_only = []
    for profile in profiles:
        channel = profile_channel(profile)
        if args.remove:
            remove_from(profile)
            print("Removed from " + str(profile))
            continue
        installed = install_into(profile, xpi)
        label = channel or "unknown edition"
        print("Installed into " + str(profile) + " (" + label + ")")
        print("  " + str(installed))
        if channel in ("release", "beta"):
            signed_only.append(profile)

    if args.remove:
        print("Quit Firefox if it is open, then start it again.")
        return 0

    if running:
        print("Firefox is running. Quit it completely, then start it again.")
    else:
        print("Start Firefox. The add-on stays installed after you quit.")

    if signed_only:
        print(
            "\nRegular Firefox and Beta will not run this unsigned file.\n"
            "Developer Edition, Nightly, and ESR will, and the signature check\n"
            "is now off in the profile for those editions.\n\n"
            "To install it in regular Firefox:\n"
            "  1. Submit dist/" + xpi.name + " at https://addons.mozilla.org/developers/\n"
            "     and choose On your own. Signing is automatic.\n"
            "  2. In Firefox, open about:addons, open the gear menu, and choose\n"
            "     Install Add-on From File. Pick the signed .xpi.\n"
            "That install stays after you quit Firefox."
        )
    else:
        print("If it is listed as disabled in about:addons, enable it there.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
