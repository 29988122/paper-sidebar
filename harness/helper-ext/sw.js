// Called over CDP by harness/cdp.mjs: buildLayout(spec) opens a fresh window with the
// tabs/groups described in harness/layouts/*.json and closes every other window.
// Tabs are self-contained data: pages with made-up content and letter favicons (no network).

function favicon(letter, color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="${color}"/>` +
    `<text x="16" y="22.5" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="700" text-anchor="middle" fill="#fff">${letter}</text></svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function page(tab) {
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const paras = (tab.body ?? [
    "This is a placeholder page used to preview the theme. It has a title, a favicon and a little text so the tab looks real.",
    "Nothing here is loaded from the network, and none of it comes from a real browsing session.",
  ]).map((p) => `<p>${esc(p)}</p>`).join("");
  const html = `<!doctype html><meta charset="utf-8"><title>${esc(tab.title)}</title>` +
    `<link rel="icon" href="${favicon(tab.letter ?? tab.title[0], tab.icon ?? "#5F6368")}">` +
    `<style>body{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;color:#1f1f1f;margin:0;background:#fff}` +
    `main{max-width:640px;margin:56px auto;padding:0 32px}h1{font-size:30px;line-height:1.25;margin:0 0 18px}p{color:#3c3c3c}` +
    `.bar{height:10px;border-radius:5px;background:#ececec;margin:14px 0}</style>` +
    `<main><h1>${esc(tab.title)}</h1>${paras}<div class="bar" style="width:92%"></div><div class="bar" style="width:84%"></div><div class="bar" style="width:66%"></div></main>`;
  return `data:text/html;charset=utf-8,${encodeURIComponent(html)}`;
}

globalThis.buildLayout = async (spec) => {
  const old = await chrome.windows.getAll();
  const win = await chrome.windows.create({ url: "about:blank", focused: true, ...spec.bounds });
  const placeholder = win.tabs[0].id;
  let activeId = null;
  const collapse = [];

  // With spec.base, pages come from harness/site.py (clean localhost URLs) instead of data: URLs.
  const slug = (title) => title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const urlFor = (tab) => tab.url ?? (spec.base ? `${spec.base}/${slug(tab.title)}` : page(tab));
  const open = async (tab) => {
    const t = await chrome.tabs.create({ windowId: win.id, url: urlFor(tab), active: false, pinned: !!tab.pinned });
    if (tab.active) activeId = t.id;
    return t.id;
  };

  for (const item of spec.items) {
    if (!item.group) {
      await open(item);
      continue;
    }
    const ids = [];
    for (const tab of item.tabs) ids.push(await open(tab));
    const groupId = await chrome.tabs.group({ tabIds: ids, createProperties: { windowId: win.id } });
    await chrome.tabGroups.update(groupId, { title: item.group, color: item.color });
    if (item.collapsed) collapse.push(groupId);
  }

  await chrome.tabs.remove(placeholder);
  if (activeId !== null) await chrome.tabs.update(activeId, { active: true });
  for (const id of collapse) await chrome.tabGroups.update(id, { collapsed: true });
  for (const w of old) await chrome.windows.remove(w.id).catch(() => {});
  await new Promise((r) => setTimeout(r, 800)); // let favicons/titles settle
  const w = await chrome.windows.get(win.id, { populate: true });
  return { windowId: w.id, left: w.left, top: w.top, width: w.width, height: w.height, tabs: w.tabs.length };
};
