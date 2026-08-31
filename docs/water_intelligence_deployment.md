# TEA Intelligence for Nontraditional Water Treatment

This feature retrieves public publication metadata from Crossref, public news from
GDELT, and any public RSS/newsletter feeds listed in
`data/intelligence/rss_sources.json`. It stores results in SQLite and asks a local
Ollama model to review and summarize only the supplied abstract or public snippet.

## 1. Install and verify Ollama on Windows

Update the NVIDIA driver first. Current Ollama releases require driver 531 or newer
for the GTX 1070/1070 Ti family.

Install Ollama, then open PowerShell:

```powershell
ollama pull qwen3:4b-instruct
ollama run qwen3:4b-instruct
```

In another PowerShell window, confirm that Ollama is using the GPU:

```powershell
nvidia-smi
```

Ollama should remain available at `http://127.0.0.1:11434`. Do not expose this port
to the internet.

## 2. Update the Python environment

From the project directory:

```powershell
conda activate tea-gui
conda env update -f environment.yml
```

For the Crossref polite API pool, set an email address:

```powershell
setx CROSSREF_MAILTO "your-email@nmsu.edu"
```

Open a new terminal after using `setx`.

## 3. Run the first collection

Start with retrieval only, which verifies sources without waiting for the model:

```powershell
python refresh_intelligence.py --no-ai
```

Then run the complete pipeline:

```powershell
python refresh_intelligence.py
```

Start the app as usual:

```powershell
python -m streamlit run TEA_GUI.py
```

Open **TEA Intelligence** in the Streamlit navigation. The generated SQLite file
is `data/intelligence/intelligence.db` and is intentionally excluded from Git.

The page separates results into **Assumption Updates**, **Technology Evidence**,
**Cost & Project Signals**, **Policy Impact**, and **Funding Opportunities**.
Related items that do not contain enough decision-grade evidence appear under the
collapsed **Background Industry News** section. Treat all model-extracted values as
review prompts and verify the linked source before changing a TEA default.

## 4. Schedule the daily refresh

In Windows Task Scheduler, create a Basic Task with a daily trigger. Configure its
action as follows:

- **Program/script:** the full path to `python.exe` in the `tea-gui` conda environment.
- **Add arguments:** the full quoted path to `refresh_intelligence.py`.
- **Start in:** the full path to the GUI project directory.

For example:

```text
Program: C:\Users\YOUR_NAME\miniconda3\envs\tea-gui\python.exe
Arguments: "C:\path\to\GUI\refresh_intelligence.py"
Start in: C:\path\to\GUI
```

Select **Run whether user is logged on or not** if this PC should perform unattended
updates. Ollama must also be running when the task begins. During alpha testing,
enable Task Scheduler history so failures are visible.

## 5. Add public newsletters or RSS feeds

Edit `data/intelligence/rss_sources.json`:

```json
[
  {
    "name": "Example public newsletter",
    "url": "https://example.org/newsletter.xml",
    "type": "Newsletter"
  }
]
```

Only add public RSS or Atom feeds. The collector does not log into email accounts,
publisher sites, or subscription services.

## Configuration

The following environment variables are optional:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` | Local summarization model |
| `INTELLIGENCE_LOOKBACK_DAYS` | `3` | Retrieval lookback window |
| `INTELLIGENCE_MAX_ITEMS` | `40` | Maximum candidates processed per run |
| `INTELLIGENCE_MIN_RULE_SCORE` | `4` | First-pass relevance threshold |
| `INTELLIGENCE_ENABLE_MANUAL_REFRESH` | `1` | Show the alpha refresh button |
| `INTELLIGENCE_DB_PATH` | `data/intelligence/intelligence.db` | SQLite database path |

For a public or shared deployment, set `INTELLIGENCE_ENABLE_MANUAL_REFRESH=0` and
let Task Scheduler run the collector.
