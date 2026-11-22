# Chat Sentinel

Chat Sentinel is an abusive-content scanner for chat logs, built with Python and [Gradio](https://www.gradio.app/). You upload a chat log, define a list of keywords, and the app scans the log for them. It was built as a final project for COP1009.

## Features

- **Upload and manage chat logs** in `.txt`, `.json`, or `.csv` format. Uploaded logs are saved in an `uploaded_logs/` folder, and you can pick or remove them from the page.
- **Configurable keyword list** stored in `keywords.json`. Add or update a keyword with an initial score, or remove one. Matching ignores upper and lower case, and a set of default keywords is restored every time the app starts.
- **Keyword scan** of the selected chat log that reports how many times each keyword appears and its score.
- **Error handling** for missing files, unreadable files, an empty keyword list, and nothing selected.

## In progress

- Per-message parsing, so each line keeps its time, user, and text
- Risk scoring with contextual rules (for example, keywords followed by `!`, or several keywords in one sentence)
- Color-coded flagged lines (green, yellow, red) with highlighted keywords
- A summary report: total lines, flagged lines, average risk score, and the top 3 riskiest lines
- A cleaned log with flagged words replaced by `[redacted]`
- Fetching a chat log from a URL

## Supported log formats

| Format | Layout |
|---|---|
| `.json` | A list of objects with `Time`, `User`, and `Message` fields |
| `.csv` | A header row of `Time,User,Message`, then one message per row |
| `.txt` | A header line, then one message per line, like `[12:14] user1: message text` |

## Usage

1. Upload a chat log, or pick one you've already uploaded from **Saved logs**.
2. Open **Additional Options** to add or remove keywords on the **Keywords** tab.
3. Go to the **Scan** tab and click **Scan for keywords**.

## Built with

- Python
- Gradio
- `requests` (for fetching logs from a URL)
