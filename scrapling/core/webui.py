from __future__ import annotations

import html
import json
import re
import threading
import uuid
import webbrowser
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from string import Template
from threading import Lock
from typing import Optional
from urllib.parse import parse_qs, parse_qsl, urlsplit

from scrapling.core.shell import Convertor
from scrapling.core.utils import log
from scrapling.fetchers import Fetcher


_PAGE_TEMPLATE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Scrapling UI</title>
  <style>
    :root {
      --bg: #f3efe8;
      --card: #fffaf0;
      --ink: #1d2a35;
      --muted: #556472;
      --accent: #0f766e;
      --accent-2: #134e4a;
      --line: #d7cfc2;
      --ok: #166534;
      --bad: #991b1b;
      --chip: #ece6db;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 0% 0%, #fef7e6 0%, transparent 40%),
        radial-gradient(circle at 100% 100%, #dff2ee 0%, transparent 35%),
        var(--bg);
      font-family: \"IBM Plex Sans\", \"Segoe UI\", sans-serif;
      min-height: 100vh;
    }
    main {
      max-width: 1100px;
      margin: 24px auto;
      padding: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 12px 30px rgba(17, 24, 39, 0.06);
      margin-bottom: 14px;
    }
    h1 { margin: 0 0 8px; font-size: 1.7rem; }
    p { margin: 0 0 12px; color: var(--muted); }
    .section-title {
      margin: 14px 0 8px;
      color: var(--muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.82rem;
    }
    label { display: block; font-weight: 600; margin: 10px 0 6px; }
    input[type=\"url\"], input[type=\"text\"], input[type=\"number\"], textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 0.97rem;
      font-family: inherit;
    }
    textarea {
      min-height: 92px;
      resize: vertical;
      font-family: \"IBM Plex Mono\", \"Cascadia Mono\", monospace;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 220px;
      gap: 12px;
    }
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .checks {
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
    }
    .check {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--chip);
      padding: 6px 10px;
      font-size: 0.92rem;
    }
    .actions {
      display: flex;
      gap: 10px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    .btn {
      border: 0;
      border-radius: 10px;
      padding: 11px 14px;
      font-weight: 700;
      color: #fff;
      background: linear-gradient(180deg, var(--accent), var(--accent-2));
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .btn.secondary {
      background: #314252;
    }
    .btn.ghost {
      background: #fff;
      color: var(--accent-2);
      border: 1px solid var(--line);
    }
    .preset-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .preset-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      background: linear-gradient(180deg, #fffef9, #fbf6eb);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .preset-card h3 {
      margin: 0;
      font-size: 1.02rem;
    }
    .preset-card p {
      margin: 0;
      font-size: 0.92rem;
    }
      .preset-toolbar {
        display: grid;
        grid-template-columns: 1fr 220px;
        gap: 10px;
        margin-bottom: 10px;
      }
      .preset-save-row {
        display: grid;
        grid-template-columns: 1fr auto auto;
        gap: 10px;
        margin-bottom: 12px;
      }
      .preset-actions {
        display: flex;
        gap: 8px;
        margin-top: auto;
        flex-wrap: wrap;
      }
      .preset-kicker {
        color: var(--muted);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
        font-weight: 700;
      }
      .btn.danger {
        background: #7f1d1d;
        color: #fff;
      }
    .status-ok { color: var(--ok); font-weight: 700; }
    .status-bad { color: var(--bad); font-weight: 700; }
    pre {
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #fff;
      padding: 12px;
      max-height: 420px;
      overflow: auto;
      font-family: \"IBM Plex Mono\", \"Cascadia Mono\", monospace;
    }
    .meta {
      margin-top: 8px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .insight-grid {
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .insight-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      padding: 10px;
    }
    .insight-title {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.84rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      font-weight: 700;
    }
    .insight-list {
      margin: 0;
      padding-left: 18px;
    }
    .insight-list li {
      margin: 3px 0;
      word-break: break-word;
      font-family: "IBM Plex Mono", "Cascadia Mono", monospace;
      font-size: 0.9rem;
    }
    .insight-note {
      margin: 0;
      color: var(--muted);
      font-size: 0.9rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 10px;
      overflow: hidden;
    }
    th, td {
      text-align: left;
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th {
      background: #f6f0e5;
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .mono {
      font-family: \"IBM Plex Mono\", \"Cascadia Mono\", monospace;
      word-break: break-word;
    }
    @media (max-width: 900px) {
      .grid-3 { grid-template-columns: 1fr; }
      .preset-grid { grid-template-columns: 1fr; }
        .preset-toolbar { grid-template-columns: 1fr; }
        .preset-save-row { grid-template-columns: 1fr; }
    }
    @media (max-width: 760px) {
      .grid-2 { grid-template-columns: 1fr; }
      .insight-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <section class=\"card\">
      <h1>Scrapling Built-in Interface</h1>
      <p>Fetch a page and extract full content or selected nodes without writing a script.</p>
      <form method=\"post\" action=\"/extract\">
        <label for=\"url\">URL</label>
        <input id=\"url\" name=\"url\" type=\"url\" required value=\"$url\" placeholder=\"https://example.com\" />

        <div class=\"grid-2\">
          <div>
            <label for=\"css_selector\">CSS Selector (optional)</label>
            <input id=\"css_selector\" name=\"css_selector\" type=\"text\" value=\"$css_selector\" placeholder=\"h1, .title, article p\" />
          </div>
          <div>
            <label for=\"fmt\">Output Format</label>
            <select id=\"fmt\" name=\"fmt\">$format_options</select>
          </div>
        </div>

        <div class=\"section-title\">Request Settings</div>
        <div class=\"grid-3\">
          <div>
            <label for=\"impersonate\">Impersonate</label>
            <input id=\"impersonate\" name=\"impersonate\" type=\"text\" value=\"$impersonate\" placeholder=\"chrome\" />
          </div>
          <div>
            <label for=\"timeout\">Timeout (seconds)</label>
            <input id=\"timeout\" name=\"timeout\" type=\"number\" min=\"1\" max=\"300\" value=\"$timeout\" />
          </div>
          <div>
            <label for=\"proxy\">Proxy (optional)</label>
            <input id=\"proxy\" name=\"proxy\" type=\"text\" value=\"$proxy\" placeholder=\"http://user:pass@host:port\" />
          </div>
        </div>

        <div class=\"grid-2\">
          <div>
            <label for=\"headers\">Headers (one per line: Key: Value)</label>
            <textarea id=\"headers\" name=\"headers\" placeholder=\"Accept-Language: en-US\nReferer: https://google.com\">$headers</textarea>
          </div>
          <div>
            <label for=\"params\">Query Params (one per line or query string)</label>
            <textarea id=\"params\" name=\"params\" placeholder=\"page=1\nq=scrapling\">$params</textarea>
          </div>
        </div>

        <label for=\"cookies\">Cookies (name1=value1; name2=value2)</label>
        <input id=\"cookies\" name=\"cookies\" type=\"text\" value=\"$cookies\" placeholder=\"session=abc123; locale=en\" />

        <div class=\"checks\">
           <label class="check"><input id="ai_targeted" type="checkbox" name="ai_targeted" $ai_checked />AI-targeted content</label>
           <label class="check"><input id="follow_redirects" type="checkbox" name="follow_redirects" $follow_redirects_checked />Follow redirects</label>
           <label class="check"><input id="verify" type="checkbox" name="verify" $verify_checked />Verify SSL</label>
           <label class="check"><input id="stealthy_headers" type="checkbox" name="stealthy_headers" $stealthy_headers_checked />Stealthy headers</label>
        </div>

        <div class=\"actions\">
          <button class=\"btn\" type=\"submit\">Fetch & Extract</button>
          <a class=\"btn secondary\" href=\"/\">Reset</a>
        </div>
      </form>
    </section>

    $preset_block
    $result_block
    $history_block
  </main>

  <script>
    const PRESETS = $presets_json;
    const STORAGE_KEY = 'scrapling.ui.savedForm';
    const CUSTOM_PRESETS_KEY = 'scrapling.ui.customPresets';

    function readField(id) {
      const element = document.getElementById(id);
      return element ? element.value : '';
    }

    function writeField(id, value) {
      const element = document.getElementById(id);
      if (element) {
        element.value = value ?? '';
      }
    }

    function setCheckbox(id, value) {
      const element = document.getElementById(id);
      if (element) {
        element.checked = Boolean(value);
      }
    }

    function readCheckbox(id) {
      const element = document.getElementById(id);
      return Boolean(element && element.checked);
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function collectCurrentForm() {
      return {
        url: readField('url'),
        css_selector: readField('css_selector'),
        fmt: readField('fmt'),
        impersonate: readField('impersonate'),
        timeout: Number(readField('timeout') || 30),
        headers_text: readField('headers'),
        params_text: readField('params'),
        cookies_text: readField('cookies'),
        proxy: readField('proxy'),
        ai_targeted: readCheckbox('ai_targeted'),
        follow_redirects: readCheckbox('follow_redirects'),
        verify: readCheckbox('verify'),
        stealthy_headers: readCheckbox('stealthy_headers')
      };
    }

    function saveState() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(collectCurrentForm()));
      } catch (error) {
        // Ignore storage errors in restricted browsers.
      }
    }

    function restoreState() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) {
          return;
        }

        const state = JSON.parse(raw);
        writeField('url', state.url);
        writeField('css_selector', state.css_selector);
        writeField('fmt', state.fmt);
        writeField('impersonate', state.impersonate);
        writeField('timeout', state.timeout);
        writeField('headers', state.headers_text);
        writeField('params', state.params_text);
        writeField('cookies', state.cookies_text);
        writeField('proxy', state.proxy);
        setCheckbox('ai_targeted', state.ai_targeted);
        setCheckbox('follow_redirects', state.follow_redirects);
        setCheckbox('verify', state.verify);
        setCheckbox('stealthy_headers', state.stealthy_headers);
      } catch (error) {
        // Ignore invalid saved state.
      }
    }

    function getCustomPresets() {
      try {
        const raw = localStorage.getItem(CUSTOM_PRESETS_KEY);
        if (!raw) {
          return {};
        }
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === 'object' ? parsed : {};
      } catch (error) {
        return {};
      }
    }

    function saveCustomPresets(customPresets) {
      try {
        localStorage.setItem(CUSTOM_PRESETS_KEY, JSON.stringify(customPresets));
      } catch (error) {
        // Ignore storage errors in restricted browsers.
      }
    }

    function getAllPresets() {
      const custom = getCustomPresets();
      return { ...PRESETS, ...custom };
    }

    function applyPreset(key) {
      const preset = getAllPresets()[key];
      if (!preset) {
        return;
      }

      writeField('url', preset.url);
      writeField('css_selector', preset.css_selector);
      writeField('fmt', preset.fmt);
      writeField('impersonate', preset.impersonate);
      writeField('timeout', preset.timeout ?? 30);
      writeField('headers', preset.headers_text || '');
      writeField('params', preset.params_text || '');
      writeField('cookies', preset.cookies_text || '');
      writeField('proxy', preset.proxy || '');
      setCheckbox('ai_targeted', preset.ai_targeted);
      setCheckbox('follow_redirects', preset.follow_redirects);
      setCheckbox('verify', preset.verify);
      setCheckbox('stealthy_headers', preset.stealthy_headers);

      saveState();
      document.getElementById('url').focus();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function slugify(value) {
      return String(value || '')
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_+|_+$/g, '');
    }

    function saveCurrentAsPreset() {
      const input = document.getElementById('custom_preset_name');
      const rawName = input ? input.value : '';
      const title = rawName.trim();
      if (!title) {
        return;
      }

      const key = `custom_${slugify(title)}`;
      const customPresets = getCustomPresets();
      customPresets[key] = {
        ...collectCurrentForm(),
        title,
        description: 'Custom preset saved from current form.',
        category: 'custom',
        group: 'custom'
      };

      saveCustomPresets(customPresets);
      if (input) {
        input.value = '';
      }
      renderPresetCards();
    }

    function deleteCustomPreset(key) {
      const customPresets = getCustomPresets();
      if (!customPresets[key]) {
        return;
      }
      delete customPresets[key];
      saveCustomPresets(customPresets);
      renderPresetCards();
    }

    function clearRememberedForm() {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (error) {
        // Ignore storage errors in restricted browsers.
      }
    }

    function matchesScope(preset, scope) {
      if (scope === 'all') {
        return true;
      }
      if (scope === 'builtin') {
        return preset.group === 'builtin';
      }
      if (scope === 'custom') {
        return preset.group === 'custom';
      }
      return preset.category === scope;
    }

    function matchesSearch(preset, query) {
      if (!query) {
        return true;
      }
      const haystack = [preset.title, preset.description, preset.category, preset.css_selector]
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    }

    function renderPresetCards() {
      const container = document.getElementById('preset_cards');
      if (!container) {
        return;
      }

      const query = (readField('preset_search') || '').trim().toLowerCase();
      const scope = readField('preset_scope') || 'all';
      const entries = Object.entries(getAllPresets())
        .filter(([, preset]) => matchesScope(preset, scope))
        .filter(([, preset]) => matchesSearch(preset, query));

      if (entries.length === 0) {
        container.innerHTML = '<div class="preset-card"><h3>No presets found</h3><p>Try another search term or filter.</p></div>';
        return;
      }

      container.innerHTML = entries
        .map(([key, preset]) => {
          const isCustom = preset.group === 'custom';
          const deleteButton = isCustom
            ? `<button class="btn danger" type="button" onclick="deleteCustomPreset('${escapeHtml(key)}')">Delete</button>`
            : '';
          return (
            `<div class="preset-card">` +
            `<div class="preset-kicker">${escapeHtml(preset.group || 'builtin')} / ${escapeHtml(preset.category || 'general')}</div>` +
            `<h3>${escapeHtml(preset.title || key)}</h3>` +
            `<p>${escapeHtml(preset.description || '')}</p>` +
            `<div class="preset-actions">` +
            `<button class="btn ghost" type="button" onclick="applyPreset('${escapeHtml(key)}')">Apply</button>` +
            deleteButton +
            `</div>` +
            `</div>`
          );
        })
        .join('');
    }

    window.applyPreset = applyPreset;
    window.deleteCustomPreset = deleteCustomPreset;

    document.addEventListener('DOMContentLoaded', () => {
      restoreState();
      renderPresetCards();

      const presetSearch = document.getElementById('preset_search');
      const presetScope = document.getElementById('preset_scope');
      const savePresetBtn = document.getElementById('save_custom_preset');
      const clearFormBtn = document.getElementById('clear_saved_form');

      if (presetSearch) {
        presetSearch.addEventListener('input', renderPresetCards);
      }
      if (presetScope) {
        presetScope.addEventListener('change', renderPresetCards);
      }
      if (savePresetBtn) {
        savePresetBtn.addEventListener('click', saveCurrentAsPreset);
      }
      if (clearFormBtn) {
        clearFormBtn.addEventListener('click', () => {
          clearRememberedForm();
          window.location.reload();
        });
      }

      document.querySelectorAll('input, textarea, select').forEach((element) => {
        element.addEventListener('input', saveState);
        element.addEventListener('change', saveState);
      });

      const form = document.querySelector('form[action="/extract"]');
      if (form) {
        form.addEventListener('submit', saveState);
      }
    });
  </script>
</body>
</html>
"""


@dataclass
class _UIFormState:
    url: str = "https://example.com"
    css_selector: str = ""
    fmt: str = "md"
    ai_targeted: bool = False
    headers_text: str = ""
    params_text: str = ""
    cookies_text: str = ""
    proxy: str = ""
    timeout: int = 30
    impersonate: str = "chrome"
    follow_redirects: bool = True
    verify: bool = True
    stealthy_headers: bool = True


@dataclass
class _ExtractResult:
    ok: bool
    status: Optional[int] = None
    output: str = ""
    message: str = ""
    download_id: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    social_links: dict[str, list[str]] = field(default_factory=dict)
    cta_links: list[str] = field(default_factory=list)
    tracker_hits: list[str] = field(default_factory=list)
    insights_download_id: str = ""


@dataclass
class _HistoryEntry:
    created_at: str
    url: str
    fmt: str
    css_selector: str
    status: Optional[int]
    ok: bool
    message: str


_HISTORY: deque[_HistoryEntry] = deque(maxlen=25)
_DOWNLOADS: dict[str, tuple[bytes, str, str]] = {}
_DOWNLOAD_ORDER: deque[str] = deque(maxlen=25)
_STATE_LOCK = Lock()

_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_HTTP_URL_PATTERN = re.compile(r"https?://[^\s<>'\"\]\)]+", re.IGNORECASE)
_HREF_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_MAILTO_PATTERN = re.compile(r"mailto:([^\s?&#\"'>]+)", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{6,}\d")
_CTA_HINTS = (
  "/contact",
  "/demo",
  "/book",
  "/pricing",
  "/trial",
  "/signup",
  "/register",
  "/get-started",
  "/quote",
  "/consult",
)

_TRACKER_SIGNATURES: dict[str, tuple[str, ...]] = {
  "Google Analytics": ("googletagmanager.com/gtag", "google-analytics.com", "gtag('config'", "ga("),
  "Google Tag Manager": ("googletagmanager.com/gtm", "gtm.js", "dataLayer.push"),
  "Meta Pixel": ("connect.facebook.net/en_US/fbevents.js", "fbq('init'", "fbq(\"init\""),
  "LinkedIn Insight": ("snap.licdn.com/li.lms-analytics/insight.min.js", "_linkedin_partner_id"),
  "TikTok Pixel": ("analytics.tiktok.com/i18n/pixel", "ttq.track", "tiktok pixel"),
  "HubSpot": ("js.hs-scripts.com", "hubspot"),
  "Segment": ("cdn.segment.com/analytics.js", "analytics.track("),
}

_SOCIAL_DOMAINS: dict[str, tuple[str, ...]] = {
    "LinkedIn": ("linkedin.com",),
    "X/Twitter": ("x.com", "twitter.com"),
    "Facebook": ("facebook.com", "fb.com"),
    "Instagram": ("instagram.com",),
    "YouTube": ("youtube.com", "youtu.be"),
    "TikTok": ("tiktok.com",),
}

_PRESETS = {
    "company_contact": {
        "title": "Company Contact Finder",
        "description": "Public email, contact pages, and footer links.",
        "category": "contact",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'footer a, a[href^="mailto:"], a[href*="contact"], a[href*="about"]',
        "fmt": "txt",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": False,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
    },
    "social_profile": {
        "title": "Social Profile Finder",
        "description": "Official LinkedIn, Instagram, X, Facebook, and YouTube links.",
        "category": "social",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href*="linkedin.com"], a[href*="instagram.com"], a[href*="x.com"], a[href*="facebook.com"], a[href*="youtube.com"]',
        "fmt": "txt",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": False,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
    },
    "lead_enrichment": {
        "title": "Lead Enrichment Finder",
        "description": "Pricing, press, partnership, and team page details.",
        "category": "lead",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href^="mailto:"], .contact, .team, .press, .partnership, .sales',
        "fmt": "md",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": True,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
    },
    "saas_competitor": {
        "title": "SaaS Competitor Snapshot",
        "description": "Collect headline, value props, pricing and CTA blocks from SaaS landing pages.",
        "category": "industry",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'h1, h2, .hero, .pricing, [class*="plan"], [class*="feature"], a[href*="pricing"]',
        "fmt": "md",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": True,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
    },
    "ecommerce_offer": {
        "title": "Ecommerce Offer Mapper",
        "description": "Capture product titles, prices, discount banners, and social links.",
        "category": "industry",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": '[class*="product"], [class*="price"], [class*="discount"], [class*="offer"], a[href*="instagram.com"], a[href*="tiktok.com"]',
        "fmt": "txt",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": False,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
    },
    "local_business_presence": {
        "title": "Local Business Presence",
        "description": "Find address, phone, opening hours, maps, and review links.",
        "category": "industry",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'address, [class*="location"], [class*="hours"], a[href^="tel:"], a[href*="maps.google"], a[href*="facebook.com"]',
        "fmt": "txt",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": False,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
    },
      "marketing_automation": {
        "title": "Marketing Automation Audit",
        "description": "Capture conversion links, social channels, contacts, and tracking signals.",
        "category": "marketing",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href], script, form, [class*="pricing"], [class*="cta"], [class*="contact"]',
        "fmt": "txt",
        "impersonate": "chrome",
        "timeout": 30,
        "ai_targeted": False,
        "follow_redirects": True,
        "verify": True,
        "stealthy_headers": True,
        "headers_text": "",
        "params_text": "",
        "cookies_text": "",
        "proxy": "",
      },
}


def _parse_headers_text(headers_text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw_line in headers_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Invalid header line: {line}")
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def _parse_cookies_text(cookies_text: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for item in cookies_text.split(";"):
        chunk = item.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(f"Invalid cookie pair: {chunk}")
        key, value = chunk.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def _parse_params_text(params_text: str) -> dict[str, str]:
    params: dict[str, str] = {}
    if not params_text.strip():
        return params

    lines = [line.strip() for line in params_text.splitlines() if line.strip()]
    for line in lines:
        if "=" in line and "&" not in line:
            key, value = line.split("=", 1)
            params[key.strip()] = value.strip()
        else:
            for key, value in parse_qsl(line, keep_blank_values=True):
                params[key.strip()] = value.strip()
    return params


def _render_format_options(selected: str) -> str:
    options = ["md", "html", "txt"]
    chunks = []
    for item in options:
        selected_attr = " selected" if item == selected else ""
        chunks.append(f'<option value="{item}"{selected_attr}>{item.upper()}</option>')
    return "".join(chunks)


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(value.strip())
    return output


def _clean_link(link: str) -> str:
    return link.strip().rstrip(".,;:!?)]}>")


def _extract_contact_insights(raw_output: str) -> tuple[list[str], list[str], list[str], dict[str, list[str]]]:
    content = html.unescape(raw_output or "")

    emails: list[str] = []
    emails.extend(_EMAIL_PATTERN.findall(content))
    emails.extend(_MAILTO_PATTERN.findall(content))
    emails = _unique_preserve_order([email.lower() for email in emails])

    phones = _unique_preserve_order(_PHONE_PATTERN.findall(content))

    discovered_links: list[str] = []
    discovered_links.extend(_HTTP_URL_PATTERN.findall(content))
    discovered_links.extend(_HREF_PATTERN.findall(content))

    links = _unique_preserve_order(
        [
            _clean_link(link)
            for link in discovered_links
            if link and link.lower().startswith(("http://", "https://"))
        ]
    )

    social_links: dict[str, list[str]] = {platform: [] for platform in _SOCIAL_DOMAINS}
    for link in links:
        parsed = urlsplit(link)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            continue

        for platform, domains in _SOCIAL_DOMAINS.items():
            if any(hostname == domain or hostname.endswith(f".{domain}") for domain in domains):
                social_links[platform].append(link)

    cleaned_social_links = {
        platform: _unique_preserve_order(platform_links)
        for platform, platform_links in social_links.items()
        if platform_links
    }

    return emails, phones, links, cleaned_social_links


def _extract_marketing_insights(raw_output: str, links: list[str]) -> tuple[list[str], list[str]]:
    content = html.unescape(raw_output or "")
    lowered = content.lower()

    cta_links = _unique_preserve_order(
        [link for link in links if any(hint in link.lower() for hint in _CTA_HINTS)]
    )

    tracker_hits: list[str] = []
    for tracker_name, signatures in _TRACKER_SIGNATURES.items():
        if any(signature.lower() in lowered for signature in signatures):
            tracker_hits.append(tracker_name)

    return cta_links, tracker_hits


def _build_marketing_payload(result: _ExtractResult, state: _UIFormState) -> str:
    payload = {
        "url": state.url,
        "format": state.fmt,
        "http_status": result.status,
        "counts": {
            "emails": len(result.emails),
            "phones": len(result.phones),
            "social_links": sum(len(items) for items in result.social_links.values()),
            "links": len(result.links),
            "cta_links": len(result.cta_links),
            "tracker_hits": len(result.tracker_hits),
        },
        "emails": result.emails,
        "phones": result.phones,
        "social_links": result.social_links,
        "cta_links": result.cta_links,
        "tracker_hits": result.tracker_hits,
        "top_links": result.links[:40],
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _convert_response(response, css_selector: str, fmt: str, ai_targeted: bool) -> str:
    extraction_type = Convertor._extension_map.get(fmt, "markdown")
    return "".join(
        Convertor._extract_content(
            response,
            extraction_type,
            css_selector=css_selector or None,
            main_content_only=ai_targeted,
        )
    )


def _cache_download(output: str, fmt: str) -> str:
    content_type = {
        "md": "text/markdown; charset=utf-8",
        "html": "text/html; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
    "json": "application/json; charset=utf-8",
    }.get(fmt, "text/plain; charset=utf-8")
    filename = f"scrapling-output.{fmt}"
    download_id = uuid.uuid4().hex

    with _STATE_LOCK:
        _DOWNLOADS[download_id] = (output.encode("utf-8", errors="replace"), content_type, filename)
        _DOWNLOAD_ORDER.append(download_id)
        while len(_DOWNLOAD_ORDER) > 20:
            old_id = _DOWNLOAD_ORDER.popleft()
            _DOWNLOADS.pop(old_id, None)

    return download_id


def _record_history(result: _ExtractResult, state: _UIFormState) -> None:
    entry = _HistoryEntry(
        created_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        url=state.url,
        fmt=state.fmt,
        css_selector=state.css_selector,
        status=result.status,
        ok=result.ok,
        message=result.message,
    )
    with _STATE_LOCK:
        _HISTORY.appendleft(entry)


def _render_result_block(result: Optional[_ExtractResult], escaped_preview: str) -> str:
    if result is None:
        return ""

    if result.ok:
        download_link = f'/download/{result.download_id}' if result.download_id else "#"
        insights_download_link = f'/download/{result.insights_download_id}' if result.insights_download_id else "#"

        email_items = (
            "".join(
                f'<li><a href="mailto:{html.escape(email)}">{html.escape(email)}</a></li>'
                for email in result.emails
            )
            if result.emails
            else '<li class="insight-note">No emails detected.</li>'
        )

        phone_items = (
            "".join(f"<li>{html.escape(phone)}</li>" for phone in result.phones)
            if result.phones
            else '<li class="insight-note">No phone numbers detected.</li>'
        )

        if result.social_links:
            social_rows = []
            for platform, links in sorted(result.social_links.items(), key=lambda item: item[0]):
                items = "".join(
                    f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(link)}</a></li>'
                    for link in links
                )
                social_rows.append(
                    '<details>'
                    f'<summary>{html.escape(platform)} ({len(links)})</summary>'
                    f'<ul class="insight-list" style="margin-top:6px">{items}</ul>'
                    '</details>'
                )
            social_block = "".join(social_rows)
        else:
            social_block = '<p class="insight-note">No social profile links detected.</p>'

        link_items = (
            "".join(
                f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(link)}</a></li>'
                for link in result.links[:40]
            )
            if result.links
            else '<li class="insight-note">No links detected.</li>'
        )

        cta_items = (
            "".join(
                f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(link)}</a></li>'
                for link in result.cta_links[:20]
            )
            if result.cta_links
            else '<li class="insight-note">No CTA links detected.</li>'
        )

        tracker_items = (
            "".join(f"<li>{html.escape(item)}</li>" for item in result.tracker_hits)
            if result.tracker_hits
            else '<li class="insight-note">No known tracker/pixel signatures detected.</li>'
        )

        stats_line = (
            f'Emails: {len(result.emails)} | '
            f'Phones: {len(result.phones)} | '
            f'Social links: {sum(len(v) for v in result.social_links.values())} | '
            f'All links: {len(result.links)} | '
            f'CTA links: {len(result.cta_links)} | '
            f'Trackers: {len(result.tracker_hits)}'
        )

        return (
            '<section class="card">'
            '<div class="status-ok">Extraction completed</div>'
            f'<div class="meta">HTTP status: {result.status}</div>'
            f'<div class="meta">{html.escape(stats_line)}</div>'
            '<div class="actions" style="margin-top:10px">'
            f'<a class="btn secondary" href="{download_link}">Download output</a>'
            f'<a class="btn ghost" href="{insights_download_link}">Download marketing JSON</a>'
            '</div>'
            '<div class="insight-grid">'
            '<div class="insight-card">'
            '<h3 class="insight-title">Detected Emails</h3>'
            f'<ul class="insight-list">{email_items}</ul>'
            '</div>'
            '<div class="insight-card">'
            '<h3 class="insight-title">Detected Phone Numbers</h3>'
            f'<ul class="insight-list">{phone_items}</ul>'
            '</div>'
            '<div class="insight-card">'
            '<h3 class="insight-title">Detected Social Links</h3>'
            f'{social_block}'
            '</div>'
            '<div class="insight-card">'
            '<h3 class="insight-title">Detected Links (Top 40)</h3>'
            f'<ul class="insight-list">{link_items}</ul>'
            '</div>'
            '<div class="insight-card">'
            '<h3 class="insight-title">Conversion / CTA Links</h3>'
            f'<ul class="insight-list">{cta_items}</ul>'
            '</div>'
            '<div class="insight-card">'
            '<h3 class="insight-title">Marketing Trackers / Pixels</h3>'
            f'<ul class="insight-list">{tracker_items}</ul>'
            '</div>'
            '</div>'
            '<label style="margin-top:10px">Preview</label>'
            f'<pre>{escaped_preview}</pre>'
            '</section>'
        )

    return (
        '<section class="card">'
        '<div class="status-bad">Extraction failed</div>'
        f'<pre>{html.escape(result.message)}</pre>'
        '</section>'
    )


def _render_preset_block() -> str:
    return (
        '<section class="card">'
    '<div class="section-title" style="margin-top:0">Preset Studio</div>'
    '<p>Search, filter, apply, and save custom presets for repeated workflows.</p>'
    '<div class="preset-toolbar">'
    '<input id="preset_search" type="text" placeholder="Search presets by name, category, or selector..." />'
    '<select id="preset_scope">'
    '<option value="all">All Presets</option>'
    '<option value="builtin">Built-in</option>'
    '<option value="custom">Custom</option>'
    '<option value="contact">Contact</option>'
    '<option value="social">Social</option>'
    '<option value="lead">Lead</option>'
    '<option value="industry">Industry</option>'
    '<option value="marketing">Marketing</option>'
    '</select>'
    '</div>'
    '<div class="preset-save-row">'
    '<input id="custom_preset_name" type="text" placeholder="Save current form as preset name..." />'
    '<button id="save_custom_preset" class="btn ghost" type="button">Save Current as Preset</button>'
    '<button id="clear_saved_form" class="btn secondary" type="button">Clear Remembered Form</button>'
    '</div>'
    '<div id="preset_cards" class="preset-grid"></div>'
        '</section>'
    )


def _render_history_block() -> str:
    with _STATE_LOCK:
        entries = list(_HISTORY)

    if not entries:
        return ""

    rows = []
    for entry in entries:
        status_text = str(entry.status) if entry.status is not None else "-"
        result_text = "OK" if entry.ok else "FAILED"
        details = html.escape(entry.message[:180]) if entry.message else ""
        selector = html.escape(entry.css_selector) if entry.css_selector else "-"
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry.created_at)}</td>"
            f"<td class=\"mono\">{html.escape(entry.url)}</td>"
            f"<td>{html.escape(entry.fmt.upper())}</td>"
            f"<td class=\"mono\">{selector}</td>"
            f"<td>{status_text}</td>"
            f"<td>{result_text}</td>"
            f"<td class=\"mono\">{details}</td>"
            "</tr>"
        )

    return (
        '<section class="card">'
        '<div class="section-title" style="margin-top:0">Recent Runs</div>'
        '<table>'
        '<thead><tr><th>Time</th><th>URL</th><th>Fmt</th><th>Selector</th><th>Status</th><th>Result</th><th>Details</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody>"
        '</table>'
        '</section>'
    )


def _render_page(
    *,
    state: Optional[_UIFormState] = None,
    result: Optional[_ExtractResult] = None,
) -> bytes:
    state = state or _UIFormState()
    escaped_output = html.escape(result.output[:20000]) if result and result.ok else ""
    page = Template(_PAGE_TEMPLATE).safe_substitute(
        preset_block=_render_preset_block(),
        result_block=_render_result_block(result, escaped_output),
        history_block=_render_history_block(),
        presets_json=json.dumps(_PRESETS, ensure_ascii=True),
        url=html.escape(state.url),
        css_selector=html.escape(state.css_selector),
        format_options=_render_format_options(state.fmt),
        ai_checked="checked" if state.ai_targeted else "",
        headers=html.escape(state.headers_text),
        params=html.escape(state.params_text),
        cookies=html.escape(state.cookies_text),
        proxy=html.escape(state.proxy),
        timeout=state.timeout,
        impersonate=html.escape(state.impersonate),
        follow_redirects_checked="checked" if state.follow_redirects else "",
        verify_checked="checked" if state.verify else "",
        stealthy_headers_checked="checked" if state.stealthy_headers else "",
    )
    return page.encode("utf-8")


def _bool_field(parsed: dict[str, list[str]], name: str, default: bool = False) -> bool:
    if name in parsed:
        return True
    return default


def _extract_from_form(form_data: bytes) -> tuple[_ExtractResult, _UIFormState]:
    parsed = parse_qs(form_data.decode("utf-8"), keep_blank_values=True)

    timeout = 30
    timeout_raw = parsed.get("timeout", ["30"])[0].strip()
    if timeout_raw:
        try:
            timeout = max(1, min(300, int(timeout_raw)))
        except ValueError:
            timeout = 30

    state = _UIFormState(
        url=parsed.get("url", [""])[0].strip(),
        css_selector=parsed.get("css_selector", [""])[0].strip(),
        fmt=parsed.get("fmt", ["md"])[0].strip().lower(),
        ai_targeted=_bool_field(parsed, "ai_targeted", default=False),
        headers_text=parsed.get("headers", [""])[0],
        params_text=parsed.get("params", [""])[0],
        cookies_text=parsed.get("cookies", [""])[0],
        proxy=parsed.get("proxy", [""])[0].strip(),
        timeout=timeout,
        impersonate=parsed.get("impersonate", ["chrome"])[0].strip() or "chrome",
        follow_redirects=_bool_field(parsed, "follow_redirects", default=False),
        verify=_bool_field(parsed, "verify", default=False),
        stealthy_headers=_bool_field(parsed, "stealthy_headers", default=False),
    )

    if state.fmt not in {"md", "html", "txt"}:
        state.fmt = "md"

    if not state.url:
        result = _ExtractResult(ok=False, message="URL is required.")
        _record_history(result, state)
        return result, state

    parsed_url = urlsplit(state.url)
    if parsed_url.scheme not in {"http", "https"}:
        result = _ExtractResult(ok=False, message="Only http/https URLs are supported.")
        _record_history(result, state)
        return result, state

    try:
        headers = _parse_headers_text(state.headers_text)
        cookies = _parse_cookies_text(state.cookies_text)
        params = _parse_params_text(state.params_text)

        response = Fetcher.get(
            state.url,
            headers=headers or None,
            cookies=cookies or None,
            params=params or None,
            timeout=state.timeout,
            proxy=state.proxy or None,
            follow_redirects=state.follow_redirects,
            verify=state.verify,
            impersonate=state.impersonate,
            stealthy_headers=state.stealthy_headers,
        )
        output = _convert_response(response, state.css_selector, state.fmt, state.ai_targeted)
        emails, phones, links, social_links = _extract_contact_insights(output)
        cta_links, tracker_hits = _extract_marketing_insights(output, links)
        result = _ExtractResult(
            ok=True,
            status=response.status,
            output=output,
            download_id=_cache_download(output, state.fmt),
            emails=emails,
            phones=phones,
            links=links,
            social_links=social_links,
            cta_links=cta_links,
            tracker_hits=tracker_hits,
        )
        result.insights_download_id = _cache_download(_build_marketing_payload(result, state), "json")
        _record_history(result, state)
        return result, state
    except Exception as exc:  # pragma: no cover
        log.exception("UI extraction failed")
        result = _ExtractResult(ok=False, message=str(exc))
        _record_history(result, state)
        return result, state


def _make_handler():
    class UIHandler(BaseHTTPRequestHandler):
        server_version = "ScraplingUI/2.0"

        def _send_html(self, body: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_response(status.value)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_download(self, download_id: str) -> None:
            with _STATE_LOCK:
                payload = _DOWNLOADS.get(download_id)

            if payload is None:
                self.send_error(HTTPStatus.NOT_FOUND.value, "Download not found")
                return

            data, content_type, filename = payload
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path == "/":
                self._send_html(_render_page())
                return

            if path.startswith("/download/"):
                download_id = path.replace("/download/", "", 1).strip()
                self._send_download(download_id)
                return

            self.send_error(HTTPStatus.NOT_FOUND.value, "Not found")

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path != "/extract":
                self.send_error(HTTPStatus.NOT_FOUND.value, "Not found")
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 128_000:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE.value, "Request body too large")
                return

            form_data = self.rfile.read(content_length)
            result, state = _extract_from_form(form_data)
            self._send_html(_render_page(state=state, result=result))

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            log.debug("UI server: " + format % args)

    return UIHandler


def run_web_ui(host: str = "127.0.0.1", port: int = 7788, open_browser: bool = False) -> None:
    """Run Scrapling's built-in local web UI."""
    handler = _make_handler()
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    log.info(f"Scrapling UI running at {url}")

    if open_browser:
        threading.Thread(target=lambda: webbrowser.open(url, new=2), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        log.info("Shutting down Scrapling UI")
    finally:
        server.server_close()
