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
    details.full-output {
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      overflow: hidden;
    }
    details.full-output summary {
      cursor: pointer;
      padding: 10px 12px;
      color: var(--accent-2);
      font-weight: 700;
      background: #f8f3e8;
      list-style: none;
    }
    details.full-output summary::-webkit-details-marker {
      display: none;
    }
    details.full-output .details-body {
      border-top: 1px solid var(--line);
      padding: 12px;
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
    .wizard {
      margin: 10px 0 14px;
      padding: 12px;
      border: 1px dashed var(--line);
      border-radius: 12px;
      background: linear-gradient(180deg, #fffdf7, #f8f2e7);
    }
    .wizard-grid {
      display: grid;
      grid-template-columns: 1.4fr 1fr auto;
      gap: 10px;
      align-items: end;
    }
    .wizard-step {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .wizard-step span {
      color: var(--muted);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      font-weight: 700;
    }
    .wizard-summary {
      margin-top: 10px;
      color: var(--muted);
      font-size: 0.9rem;
    }
    @media (max-width: 900px) {
      .wizard-grid { grid-template-columns: 1fr; }
      .wizard-grid .btn { width: 100%; }
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

      <div class=\"wizard\">
        <div class=\"section-title\" style=\"margin-top:0\">Guided Mode</div>
        <div class=\"wizard-grid\">
          <label class=\"wizard-step\" for=\"wizard_url\">
            <span>Step 1: URL</span>
            <input id=\"wizard_url\" type=\"url\" placeholder=\"https://example.com\" />
          </label>
          <label class=\"wizard-step\" for=\"wizard_goal\">
            <span>Step 2: Goal</span>
            <select id=\"wizard_goal\">
              <option value=\"contact\">Contact</option>
              <option value=\"lead\">Lead</option>
              <option value=\"competitor\">Competitor</option>
              <option value=\"marketing\">Marketing</option>
            </select>
          </label>
          <button id=\"wizard_apply_run\" class=\"btn\" type=\"button\">Step 3: Smart Defaults + Run</button>
        </div>
        <div id=\"wizard_summary\" class=\"wizard-summary\"></div>
      </div>

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

    $dashboard_block
    $preset_block
    $result_block
    $batch_result_block
    $history_block
  </main>

  <script>
    const PRESETS = $presets_json;
    const STORAGE_KEY = 'scrapling.ui.savedForm';
    const CUSTOM_PRESETS_KEY = 'scrapling.ui.customPresets';
    const GOAL_PRESET_MAP = {
      contact: 'company_contact',
      lead: 'saas_lead_hunt',
      competitor: 'saas_competitor',
      marketing: 'marketing_stack_hunt'
    };
    const GOAL_SUMMARY_MAP = {
      contact: 'Contact goal uses email/contact-focused selectors and TXT output for clean lead extraction.',
      lead: 'Lead goal uses conversion and sales-oriented selectors with scoring-friendly defaults.',
      competitor: 'Competitor goal captures headline, value props, pricing, and CTA blocks from landing pages.',
      marketing: 'Marketing goal prioritizes script and link signals to detect tracking and stack fingerprints.'
    };

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

    function downloadTextFile(filename, content, mimeType) {
      const blob = new Blob([content], { type: mimeType });
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    }

    function exportCustomPresets() {
      const presets = getCustomPresets();
      const content = JSON.stringify(presets, null, 2);
      downloadTextFile('scrapling-custom-presets.json', content, 'application/json');
    }

    async function importCustomPresetsFromFile(file) {
      if (!file) {
        return;
      }

      const text = await file.text();
      const parsed = JSON.parse(text);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('Preset file must contain a JSON object.');
      }

      const current = getCustomPresets();
      Object.entries(parsed).forEach(([key, preset]) => {
        if (preset && typeof preset === 'object' && preset.title) {
          current[key] = preset;
        }
      });

      saveCustomPresets(current);
      renderPresetCards();
    }

    async function importCustomPresets() {
      const input = document.getElementById('import_custom_presets');
      const file = input && input.files ? input.files[0] : null;
      if (!file) {
        return;
      }

      try {
        await importCustomPresetsFromFile(file);
        if (input) {
          input.value = '';
        }
      } catch (error) {
        alert(error instanceof Error ? error.message : 'Unable to import presets.');
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

    function updateWizardSummary() {
      const goal = readField('wizard_goal') || 'contact';
      const summary = document.getElementById('wizard_summary');
      if (!summary) {
        return;
      }

      const presetKey = GOAL_PRESET_MAP[goal];
      const preset = getAllPresets()[presetKey];
      const goalText = GOAL_SUMMARY_MAP[goal] || 'Goal selected.';
      const presetTitle = preset && preset.title ? preset.title : 'No preset';
      summary.textContent = `Smart defaults: ${presetTitle}. ${goalText}`;
    }

    function runGuidedFlow() {
      const wizardUrl = (readField('wizard_url') || '').trim();
      const goal = readField('wizard_goal') || 'contact';
      const presetKey = GOAL_PRESET_MAP[goal];
      const form = document.querySelector('form[action="/extract"]');

      if (!wizardUrl || !form) {
        return;
      }

      try {
        const parsed = new URL(wizardUrl);
        if (!['http:', 'https:'].includes(parsed.protocol)) {
          alert('Only http/https URLs are supported.');
          return;
        }
      } catch (error) {
        alert('Please enter a valid URL.');
        return;
      }

      if (presetKey) {
        applyPreset(presetKey);
      }
      writeField('url', wizardUrl);
      saveState();
      form.submit();
    }

    window.applyPreset = applyPreset;
    window.deleteCustomPreset = deleteCustomPreset;
    window.exportCustomPresets = exportCustomPresets;
    window.importCustomPresets = importCustomPresets;

    document.addEventListener('DOMContentLoaded', () => {
      restoreState();
      renderPresetCards();

      const presetSearch = document.getElementById('preset_search');
      const presetScope = document.getElementById('preset_scope');
      const savePresetBtn = document.getElementById('save_custom_preset');
      const exportPresetBtn = document.getElementById('export_custom_presets');
      const importPresetBtn = document.getElementById('import_custom_presets_btn');
      const clearFormBtn = document.getElementById('clear_saved_form');
      const wizardUrl = document.getElementById('wizard_url');
      const wizardGoal = document.getElementById('wizard_goal');
      const wizardApplyRunBtn = document.getElementById('wizard_apply_run');

      if (wizardUrl) {
        wizardUrl.value = readField('url') || '';
      }
      updateWizardSummary();

      if (presetSearch) {
        presetSearch.addEventListener('input', renderPresetCards);
      }
      if (presetScope) {
        presetScope.addEventListener('change', renderPresetCards);
      }
      if (savePresetBtn) {
        savePresetBtn.addEventListener('click', saveCurrentAsPreset);
      }
      if (exportPresetBtn) {
        exportPresetBtn.addEventListener('click', exportCustomPresets);
      }
      if (importPresetBtn) {
        importPresetBtn.addEventListener('click', importCustomPresets);
      }
      if (clearFormBtn) {
        clearFormBtn.addEventListener('click', () => {
          clearRememberedForm();
          window.location.reload();
        });
      }
      if (wizardGoal) {
        wizardGoal.addEventListener('change', updateWizardSummary);
      }
      if (wizardApplyRunBtn) {
        wizardApplyRunBtn.addEventListener('click', runGuidedFlow);
      }

      document.querySelectorAll('input, textarea, select').forEach((element) => {
        element.addEventListener('input', saveState);
        element.addEventListener('change', saveState);
      });
      if (wizardUrl) {
        wizardUrl.addEventListener('input', () => {
          writeField('url', wizardUrl.value);
          saveState();
        });
      }

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
    lead_score: int = 0
    comparison_summary: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    social_links: dict[str, list[str]] = field(default_factory=dict)
    cta_links: list[str] = field(default_factory=list)
    tracker_hits: list[str] = field(default_factory=list)
    insights_download_id: str = ""


@dataclass
class _BatchRow:
    url: str
    status: Optional[int] = None
    ok: bool = False
    lead_score: int = 0
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    cta_links: list[str] = field(default_factory=list)
    tracker_hits: list[str] = field(default_factory=list)
    social_links: dict[str, list[str]] = field(default_factory=dict)
    error: str = ""


@dataclass
class _BatchResult:
    ok: bool
    total_urls: int = 0
    success_count: int = 0
    failed_count: int = 0
    rows: list[_BatchRow] = field(default_factory=list)
    message: str = ""
    download_id: str = ""
    csv_download_id: str = ""


@dataclass
class _HistoryEntry:
    created_at: str
    url: str
    fmt: str
    css_selector: str
    status: Optional[int]
    ok: bool
    message: str
    lead_score: int
    email_count: int
    phone_count: int
    link_count: int
    cta_count: int
    tracker_count: int


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
      "saas_lead_hunt": {
        "title": "SaaS Lead Hunt",
        "description": "Hunt decision-maker contact points plus demo and pricing conversion links.",
        "category": "lead",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href], [class*="contact"], [class*="sales"], [class*="demo"], [class*="pricing"], footer',
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
      "agency_prospect_hunt": {
        "title": "Agency Client Prospect Hunt",
        "description": "Collect direct email, phone, contact pages, and local business profile links.",
        "category": "lead",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href^="mailto:"], a[href^="tel:"], a[href*="contact"], a[href*="about"], address, footer',
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
      "ecommerce_intel_hunt": {
        "title": "Ecommerce Offer Intelligence Hunt",
        "description": "Capture products, discount offers, and checkout-oriented conversion links.",
        "category": "industry",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href], [class*="product"], [class*="price"], [class*="discount"], [class*="offer"], [class*="cart"], [class*="checkout"]',
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
      "marketing_stack_hunt": {
        "title": "Marketing Stack Hunt",
        "description": "Detect trackers, pixels, and script-level marketing stack signals.",
        "category": "marketing",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": "script, noscript, a[href], head",
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
      "bulk_competitor_hunt": {
        "title": "Bulk Competitor Hunt",
        "description": "Use these selectors with the Marketing Dashboard bulk audit for side-by-side URL scoring.",
        "category": "marketing",
        "group": "builtin",
        "url": "https://example.com",
        "css_selector": 'a[href], script, [class*="pricing"], [class*="contact"], [class*="demo"]',
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


def _calculate_lead_score(result: _ExtractResult) -> int:
  score = 0
  score += min(len(result.emails) * 20, 40)
  score += min(len(result.phones) * 12, 24)
  score += min(sum(len(items) for items in result.social_links.values()) * 8, 24)
  score += min(len(result.cta_links) * 10, 20)
  score += min(len(result.tracker_hits) * 3, 9)
  if result.status and 200 <= result.status < 400:
    score += 10
  return min(score, 100)


def _lead_score_label(score: int) -> str:
  if score >= 80:
    return "Hot"
  if score >= 55:
    return "Warm"
  if score >= 30:
    return "Nurture"
  return "Cold"


def _build_run_comparison(result: _ExtractResult, state: _UIFormState) -> str:
  previous_entry = next((entry for entry in _HISTORY if entry.url == state.url), None)
  if previous_entry is None:
    return ""

  deltas = []

  def _format_delta(label: str, value: int) -> str:
    if value == 0:
      return f"{label}: no change"
    prefix = "+" if value > 0 else ""
    return f"{label}: {prefix}{value}"

  deltas.append(_format_delta("Emails", len(result.emails) - previous_entry.email_count))
  deltas.append(_format_delta("Phones", len(result.phones) - previous_entry.phone_count))
  deltas.append(_format_delta("CTA links", len(result.cta_links) - previous_entry.cta_count))
  deltas.append(_format_delta("Trackers", len(result.tracker_hits) - previous_entry.tracker_count))

  score_delta = result.lead_score - previous_entry.lead_score
  score_prefix = "+" if score_delta > 0 else ""
  return (
    "Compared with the previous run for this URL: "
    f"score {score_prefix}{score_delta}; "
    + "; ".join(deltas)
  )


def _build_marketing_payload(result: _ExtractResult, state: _UIFormState) -> str:
    payload = {
        "url": state.url,
        "format": state.fmt,
        "http_status": result.status,
    "lead_score": result.lead_score,
    "comparison_summary": result.comparison_summary,
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


def _normalize_bulk_urls(raw_urls: str) -> list[str]:
    urls: list[str] = []
    for raw_line in raw_urls.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for candidate in re.split(r"[\s,]+", line):
            candidate = candidate.strip()
            if not candidate:
                continue
            parsed = urlsplit(candidate)
            if parsed.scheme not in {"http", "https"}:
                continue
            urls.append(candidate)
    return _unique_preserve_order(urls)


def _build_batch_payload(result: _BatchResult) -> str:
    payload = {
        "ok": result.ok,
        "total_urls": result.total_urls,
        "success_count": result.success_count,
        "failed_count": result.failed_count,
        "rows": [
            {
                "url": row.url,
                "ok": row.ok,
                "status": row.status,
                "lead_score": row.lead_score,
                "emails": row.emails,
                "phones": row.phones,
                "links": row.links,
                "cta_links": row.cta_links,
                "tracker_hits": row.tracker_hits,
                "social_links": row.social_links,
                "error": row.error,
            }
            for row in result.rows
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _build_batch_csv(result: _BatchResult) -> str:
    header = "url,ok,status,lead_score,emails,phones,links,cta_links,tracker_hits,error"
    lines = [header]
    for row in result.rows:
        lines.append(
            ",".join(
                [
                    json.dumps(row.url)[1:-1],
                    "true" if row.ok else "false",
                    str(row.status if row.status is not None else ""),
                    str(row.lead_score),
                    str(len(row.emails)),
                    str(len(row.phones)),
                    str(len(row.links)),
                    str(len(row.cta_links)),
                    str(len(row.tracker_hits)),
                    json.dumps(row.error)[1:-1],
                ]
            )
        )
    return "\n".join(lines)


def _extract_batch_from_form(form_data: bytes) -> tuple[_BatchResult, list[str]]:
    parsed = parse_qs(form_data.decode("utf-8"), keep_blank_values=True)
    urls = _normalize_bulk_urls(parsed.get("bulk_urls", [""])[0])
    if not urls:
        result = _BatchResult(ok=False, message="At least one valid http/https URL is required.")
        return result, []

    timeout = 30
    timeout_raw = parsed.get("bulk_timeout", ["30"])[0].strip()
    if timeout_raw:
        try:
            timeout = max(1, min(300, int(timeout_raw)))
        except ValueError:
            timeout = 30

    state = _UIFormState(
        css_selector=parsed.get("bulk_css_selector", [""])[0].strip(),
        fmt=parsed.get("bulk_fmt", ["txt"])[0].strip().lower(),
        headers_text=parsed.get("bulk_headers", [""])[0],
        params_text=parsed.get("bulk_params", [""])[0],
        cookies_text=parsed.get("bulk_cookies", [""])[0],
        proxy=parsed.get("bulk_proxy", [""])[0].strip(),
        timeout=timeout,
        impersonate=parsed.get("bulk_impersonate", ["chrome"])[0].strip() or "chrome",
        follow_redirects=_bool_field(parsed, "bulk_follow_redirects", default=False),
        verify=_bool_field(parsed, "bulk_verify", default=False),
        stealthy_headers=_bool_field(parsed, "bulk_stealthy_headers", default=False),
        ai_targeted=_bool_field(parsed, "bulk_ai_targeted", default=False),
    )

    if state.fmt not in {"md", "html", "txt"}:
        state.fmt = "txt"

    rows: list[_BatchRow] = []
    success_count = 0
    failed_count = 0

    try:
        headers = _parse_headers_text(state.headers_text)
        cookies = _parse_cookies_text(state.cookies_text)
        params = _parse_params_text(state.params_text)

        for url in urls[:20]:
            row = _BatchRow(url=url)
            try:
                response = Fetcher.get(
                    url,
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
                row.status = response.status
                row.ok = True
                row.lead_score = _calculate_lead_score(
                  _ExtractResult(
                    ok=True,
                    status=response.status,
                    emails=emails,
                    phones=phones,
                    links=links,
                    social_links=social_links,
                    cta_links=cta_links,
                    tracker_hits=tracker_hits,
                  )
                )
                row.emails = emails
                row.phones = phones
                row.links = links
                row.social_links = social_links
                row.cta_links = cta_links
                row.tracker_hits = tracker_hits
                success_count += 1
            except Exception as exc:  # pragma: no cover
                row.ok = False
                row.error = str(exc)
                failed_count += 1
            rows.append(row)

        batch_result = _BatchResult(
            ok=True,
            total_urls=len(urls[:20]),
            success_count=success_count,
            failed_count=failed_count,
            rows=rows,
        )
        batch_result.download_id = _cache_download(_build_batch_payload(batch_result), "json")
        batch_result.csv_download_id = _cache_download(_build_batch_csv(batch_result), "csv")
        return batch_result, urls
    except Exception as exc:  # pragma: no cover
        log.exception("Bulk marketing audit failed")
        return _BatchResult(ok=False, message=str(exc)), urls


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
    "csv": "text/csv; charset=utf-8",
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
    lead_score=result.lead_score,
    email_count=len(result.emails),
    phone_count=len(result.phones),
    link_count=len(result.links),
    cta_count=len(result.cta_links),
    tracker_count=len(result.tracker_hits),
    )
    with _STATE_LOCK:
        _HISTORY.appendleft(entry)


def _render_result_block(result: Optional[_ExtractResult], escaped_preview: str) -> str:
    if result is None:
        return ""

    if result.ok:
        download_link = f'/download/{result.download_id}' if result.download_id else "#"
        insights_download_link = f'/download/{result.insights_download_id}' if result.insights_download_id else "#"
        lead_score_label = _lead_score_label(result.lead_score)
        comparison_block = f'<div class="meta">{html.escape(result.comparison_summary)}</div>' if result.comparison_summary else ""
        full_output = html.escape(result.output)

        email_items = "".join(
            f'<li><a href="mailto:{html.escape(email)}">{html.escape(email)}</a></li>'
            for email in result.emails
        ) or '<li class="insight-note">No emails detected.</li>'
        phone_items = "".join(f"<li>{html.escape(phone)}</li>" for phone in result.phones) or '<li class="insight-note">No phone numbers detected.</li>'
        link_items = "".join(
            f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(link)}</a></li>'
            for link in result.links[:20]
        ) or '<li class="insight-note">No links detected.</li>'
        cta_items = "".join(
            f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{html.escape(link)}</a></li>'
            for link in result.cta_links[:20]
        ) or '<li class="insight-note">No CTA links detected.</li>'
        tracker_items = "".join(f"<li>{html.escape(item)}</li>" for item in result.tracker_hits) or '<li class="insight-note">No known tracker/pixel signatures detected.</li>'
        social_summary = ", ".join(f"{platform}: {len(links)}" for platform, links in sorted(result.social_links.items())) or "No social profile links detected."
        stats_line = (
            f'Emails: {len(result.emails)} | Phones: {len(result.phones)} | '
            f'Social links: {sum(len(v) for v in result.social_links.values())} | '
            f'All links: {len(result.links)} | CTA links: {len(result.cta_links)} | Trackers: {len(result.tracker_hits)}'
        )

        return (
            '<section class="card">'
            '<div class="status-ok">Extraction completed</div>'
            f'<div class="meta"><strong>Lead score:</strong> {result.lead_score}/100 ({html.escape(lead_score_label)})</div>'
            f'<div class="meta">HTTP status: {result.status}</div>'
            f'<div class="meta">{html.escape(stats_line)}</div>'
            f'{comparison_block}'
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
            f'<p class="insight-note">{html.escape(social_summary)}</p>'
            '</div>'
            '<div class="insight-card">'
            '<h3 class="insight-title">Detected Links</h3>'
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
            '<details class="full-output">'
            '<summary>Show full output</summary>'
            '<div class="details-body">'
            '<div class="meta" style="margin-top:0">Full extracted result, unchanged from the backend response.</div>'
            f'<pre>{full_output}</pre>'
            '</div>'
            '</details>'
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
    '<button id="export_custom_presets" class="btn secondary" type="button">Export Custom Presets</button>'
    '</div>'
    '<div class="preset-save-row">'
    '<input id="import_custom_presets" type="file" accept="application/json" />'
    '<button id="import_custom_presets_btn" class="btn ghost" type="button">Import Custom Presets</button>'
    '<button id="clear_saved_form" class="btn secondary" type="button">Clear Remembered Form</button>'
    '</div>'
    '<div id="preset_cards" class="preset-grid"></div>'
        '</section>'
    )


def _render_dashboard_block(state: Optional[_UIFormState] = None) -> str:
    state = state or _UIFormState()
    bulk_urls = html.escape(state.url)
    return (
        '<section class="card">'
        '<div class="section-title" style="margin-top:0">Marketing Dashboard</div>'
        '<p>Paste multiple URLs, reuse the same request settings, and inspect contact, CTA, and tracker signals in one pass.</p>'
        '<form method="post" action="/batch">'
        '<label for="bulk_urls">Bulk URLs (one per line)</label>'
        f'<textarea id="bulk_urls" name="bulk_urls" placeholder="https://example.com\nhttps://example.org">{bulk_urls}</textarea>'
        '<div class="grid-2">'
        '<div>'
        '<label for="bulk_css_selector">Bulk CSS Selector (optional)</label>'
        f'<input id="bulk_css_selector" name="bulk_css_selector" type="text" value="{html.escape(state.css_selector)}" placeholder="a[href], form, script" />'
        '</div>'
        '<div>'
        '<label for="bulk_fmt">Bulk Output Format</label>'
        f'<select id="bulk_fmt" name="bulk_fmt">{_render_format_options(state.fmt)}</select>'
        '</div>'
        '</div>'
        '<div class="grid-3">'
        '<div>'
        '<label for="bulk_impersonate">Impersonate</label>'
        f'<input id="bulk_impersonate" name="bulk_impersonate" type="text" value="{html.escape(state.impersonate)}" />'
        '</div>'
        '<div>'
        '<label for="bulk_timeout">Timeout (seconds)</label>'
        f'<input id="bulk_timeout" name="bulk_timeout" type="number" min="1" max="300" value="{state.timeout}" />'
        '</div>'
        '<div>'
        '<label for="bulk_proxy">Proxy (optional)</label>'
        f'<input id="bulk_proxy" name="bulk_proxy" type="text" value="{html.escape(state.proxy)}" placeholder="http://user:pass@host:port" />'
        '</div>'
        '</div>'
        '<div class="actions">'
        '<button class="btn" type="submit">Run Dashboard Audit</button>'
        '<a class="btn secondary" href="/">Reset</a>'
        '</div>'
        '</form>'
        '</section>'
    )


def _render_batch_result_block(result: Optional[_BatchResult]) -> str:
    if result is None:
        return ""

    if not result.ok:
        return (
            '<section class="card">'
            '<div class="status-bad">Bulk audit failed</div>'
            f'<pre>{html.escape(result.message)}</pre>'
            '</section>'
        )

    rows = []
    for row in result.rows:
        rows.append(
            '<tr>'
            f'<td class="mono">{html.escape(row.url)}</td>'
            f'<td>{"OK" if row.ok else "FAILED"}</td>'
            f'<td>{row.status if row.status is not None else "-"}</td>'
            f'<td>{row.lead_score}</td>'
            f'<td>{len(row.emails)}</td>'
            f'<td>{len(row.phones)}</td>'
            f'<td>{len(row.cta_links)}</td>'
            f'<td>{len(row.tracker_hits)}</td>'
            f'<td class="mono">{html.escape(row.error[:160]) if row.error else "-"}</td>'
            '</tr>'
        )

    return (
        '<section class="card">'
        '<div class="status-ok">Bulk audit completed</div>'
        f'<div class="meta">Processed: {result.total_urls} | Success: {result.success_count} | Failed: {result.failed_count}</div>'
        '<div class="actions" style="margin-top:10px">'
        f'<a class="btn secondary" href="{f"/download/{result.download_id}" if result.download_id else "#"}">Download JSON</a>'
        f'<a class="btn ghost" href="{f"/download/{result.csv_download_id}" if result.csv_download_id else "#"}">Download CSV</a>'
        '</div>'
        '<table style="margin-top:12px">'
        '<thead><tr><th>URL</th><th>Status</th><th>HTTP</th><th>Score</th><th>Emails</th><th>Phones</th><th>CTA</th><th>Trackers</th><th>Notes</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody>"
        '</table>'
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
            f"<td>{entry.lead_score}</td>"
            f"<td>{result_text}</td>"
            f"<td class=\"mono\">{details}</td>"
            "</tr>"
        )

    return (
        '<section class="card">'
        '<div class="section-title" style="margin-top:0">Recent Runs</div>'
        '<table>'
        '<thead><tr><th>Time</th><th>URL</th><th>Fmt</th><th>Selector</th><th>Status</th><th>Score</th><th>Result</th><th>Details</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody>"
        '</table>'
        '</section>'
    )


def _render_page(
    *,
    state: Optional[_UIFormState] = None,
    result: Optional[_ExtractResult] = None,
  batch_result: Optional[_BatchResult] = None,
) -> bytes:
    state = state or _UIFormState()
    escaped_output = html.escape(result.output[:20000]) if result and result.ok else ""
    page = Template(_PAGE_TEMPLATE).safe_substitute(
    dashboard_block=_render_dashboard_block(state),
        preset_block=_render_preset_block(),
        result_block=_render_result_block(result, escaped_output),
    batch_result_block=_render_batch_result_block(batch_result),
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
        result.lead_score = _calculate_lead_score(result)
        result.comparison_summary = _build_run_comparison(result, state)
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
            if path not in {"/extract", "/batch"}:
                self.send_error(HTTPStatus.NOT_FOUND.value, "Not found")
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 128_000:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE.value, "Request body too large")
                return

            form_data = self.rfile.read(content_length)
            if path == "/extract":
                result, state = _extract_from_form(form_data)
                self._send_html(_render_page(state=state, result=result))
                return

            batch_result, urls = _extract_batch_from_form(form_data)
            batch_state = _UIFormState(url=urls[0] if urls else "")
            self._send_html(_render_page(state=batch_state, batch_result=batch_result))

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
