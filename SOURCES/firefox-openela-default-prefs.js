pref("app.update.auto",                     false);
pref("app.update.enabled",                  false);
pref("app.update.autoInstallEnabled",       false);
pref("general.smoothScroll",                true);
pref("intl.locale.requested",               "");
pref("toolkit.storage.synchronous",         0);
pref("toolkit.networkmanager.disable",      false);
pref("offline.autoDetect",                  true);
pref("browser.backspace_action",            2);
pref("browser.display.use_system_colors",   true);
pref("browser.download.folderList",         1);
pref("browser.link.open_external",          3);
pref("browser.shell.checkDefaultBrowser",   false);
pref("network.manage-offline-status",       true);
pref("extensions.shownSelectionUI",         true);
pref("ui.SpellCheckerUnderlineStyle",       1);
pref("startup.homepage_override_url",       "https://openela.org");
pref("startup.homepage_welcome_url",        "https://openela.org");
pref("browser.startup.homepage",            "data:text/plain,browser.startup.homepage=file:///usr/share/doc/HTML/index.html");
pref("geo.wifi.uri", "https://location.services.mozilla.com/v1/geolocate?key=%MOZILLA_API_KEY%");
pref("media.gmp-gmpopenh264.provider.enabled",false);
pref("media.gmp-gmpopenh264.autoupdate",false);
pref("media.gmp-gmpopenh264.enabled",false);
pref("media.gmp.decoder.enabled", true);
pref("plugins.notifyMissingFlash", false);
/* See https://bugzilla.redhat.com/show_bug.cgi?id=1226489 */
pref("browser.display.use_system_colors", false);
pref("layers.use-image-offscreen-surfaces", false);
/* Allow sending credetials to all https:// sites */
pref("network.negotiate-auth.trusted-uris", "https://");
pref("security.use_sqldb", false);
pref("spellchecker.dictionary_path","/usr/share/myspell");
/* Disable DoH by default */
pref("network.trr.mode",                    5);
/* Enable per-user policy dir, see mozbz#1583466 */
pref("browser.policies.perUserDir",         true);
pref("browser.gnome-search-provider.enabled",true);
/* Enable ffvpx playback for WebRTC */
pref("media.navigator.mediadatadecoder_vpx_enabled", true);
/* See https://bugzilla.redhat.com/show_bug.cgi?id=1672424 */
pref("storage.nfs_filesystem", true);
