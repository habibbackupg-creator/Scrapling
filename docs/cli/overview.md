# Command Line Interface

Since v0.3, Scrapling includes a powerful command-line interface that provides four main capabilities:

1. **Interactive Shell**: An interactive Web Scraping shell based on IPython that provides many shortcuts and useful tools
2. **Extract Commands**: Scrape websites from the terminal without any programming
3. **Built-in Web Interface**: Open a local UI to fetch a page and preview extracted output
4. **Utility Commands**: Installation and management tools

```bash
# Launch interactive shell
scrapling shell

# Convert the content of a page to markdown and save it to a file
scrapling extract get "https://example.com" content.md

# Get help for any command
scrapling --help
scrapling extract --help

# Open the built-in local web interface
scrapling ui --open-browser
```

### Built-in Web Interface (Real-world workflow)
Use the built-in UI when you want a full extraction workflow without writing scripts.

- Supports URL + CSS selector extraction
- Supports output formats (`md`, `html`, `txt`)
- Supports request controls: headers, cookies, query params, proxy, timeout, impersonation
- Supports behavior toggles: AI-targeted extraction, redirect following, SSL verification, stealthy headers
- Includes a download button for the extracted output
- Includes a recent run history panel for quick troubleshooting
- Includes ready-made presets for public business research and contact discovery

```bash
scrapling ui --host 127.0.0.1 --port 7788 --open-browser
```

Then use the browser UI at `http://127.0.0.1:7788/`.

#### Ready-Made Presets
These are safe defaults for public business data only.

**Company Contact Finder**
- URL: company homepage
- CSS Selector: `footer a, a[href^="mailto:"], a[href*="contact"], a[href*="about"]`
- Output Format: `txt`

**Social Profile Finder**
- URL: homepage or about page
- CSS Selector: `a[href*="linkedin.com"], a[href*="instagram.com"], a[href*="x.com"], a[href*="facebook.com"], a[href*="youtube.com"]`
- Output Format: `txt`

**Lead Enrichment Finder**
- URL: pricing, contact, partnership, press, or team page
- CSS Selector: `a[href^="mailto:"], .contact, .team, .press, .partnership, .sales`
- Output Format: `md`

## Requirements
This section requires you to install the extra `shell` dependency group, like the following:
```bash
pip install "scrapling[shell]"
```
and the installation of the fetchers' dependencies with the following command
```bash
scrapling install
```
This downloads all browsers, along with their system dependencies and fingerprint manipulation dependencies.