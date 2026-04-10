# Web UI User Guide

Scrapling includes a built-in web interface for quick extraction without writing scripts.

This guide covers:

- How to start the app
- What each field does
- Typical workflows
- Troubleshooting

## Who this is for

Use the Web UI if you want to:

- Test extraction settings quickly
- Share a simple extraction workflow with non-developers
- Inspect output before writing code

## Prerequisites

Install Scrapling with shell support and fetcher dependencies:

```bash
pip install "scrapling[shell]"
scrapling install
```

## Start the app

Run locally:

```bash
scrapling ui --host 127.0.0.1 --port 7788 --open-browser
```

Then open:

```text
http://127.0.0.1:7788/
```

### Useful startup options

- `--host`: bind interface (`127.0.0.1` by default)
- `--port`: listening port (`7788` by default)
- `--open-browser` / `--no-open-browser`: auto-open browser

## Interface walkthrough

### 1) URL

Target page to fetch, for example:

```text
https://example.com
```

### 2) CSS Selector (optional)

If empty, the app returns full page output in your selected format.

If provided, only matching nodes are extracted.

Examples:

- `h1`
- `.product-title`
- `article p`

### 3) Output format

- `md`: Markdown output
- `html`: Raw HTML output
- `txt`: Plain text output

### 4) Request settings

- `Impersonate`: browser profile hint (example: `chrome`)
- `Timeout`: request timeout in seconds
- `Proxy`: proxy URL, for example `http://user:pass@host:port`
- `Headers`: one header per line in `Key: Value` format
- `Query Params`: either one `key=value` per line or a query string style input
- `Cookies`: semicolon-separated string, for example `session=abc; locale=en`

### 5) Behavior toggles

- `AI-targeted content`: returns cleaner, main-content-focused output
- `Follow redirects`: follow HTTP redirects
- `Verify SSL`: validate TLS/SSL certificates
- `Stealthy headers`: use stealth-oriented headers

### 6) Actions

- `Fetch & Extract`: executes request + extraction
- `Reset`: clears form values to defaults

## Result and history panels

After each run, the app shows:

- Status (success or error)
- Output preview
- Metadata (url, selector, format, options)
- Recent history for quick comparison and retries

## Typical workflows

### Workflow A: quick text extraction

1. Enter URL
2. Set format to `txt`
3. Leave selector empty
4. Click `Fetch & Extract`

### Workflow B: extract selected blocks

1. Enter URL
2. Set selector (example: `.post-content p`)
3. Choose `md`
4. Click `Fetch & Extract`

### Workflow C: protected site with custom settings

1. Set `Impersonate` to `chrome`
2. Enable `Stealthy headers`
3. Add custom headers/cookies if needed
4. Increase timeout
5. Click `Fetch & Extract`

## Troubleshooting

### UI does not open

- Confirm command was started without errors
- Check host/port values
- Try another port (example: `--port 7799`)

### Connection refused in browser

- Service may not be listening on that port
- If running in container/server, confirm port exposure and firewall rules

### Empty extraction result

- CSS selector may not match current DOM
- Try without selector first
- Try a broader selector and narrow down gradually

### SSL or proxy related failures

- Verify proxy URL format
- Temporarily disable strict SSL check (`Verify SSL` off) for testing only

## Security and data handling notes

- Do not paste sensitive credentials unless needed
- Prefer short-lived tokens/cookies for testing
- Avoid storing production secrets in shared environments

## Next step

Once your UI flow works, move the same settings to scripted usage with:

- `scrapling extract` commands
- Python fetcher classes for automation
