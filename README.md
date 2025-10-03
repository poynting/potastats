# POTA Activator Stats

A small CLI tool that downloads and processes the **Parks on the Air (POTA) activator dataset** from  
<https://api.pota.app/activator/all> and reports high-level statistics:

- Total number of contacts across all activators
- Contacts per mode (CW, Data, Phone)
- Percentages per mode

Features:
- **Progress bar** during download (`tqdm`)
- **Local caching** to avoid re-downloading on every run
- **Auto-refresh** based on cache age or `--refresh` flag

---

## Quickstart

(optional) create and activate a virtual environment
```bash
python3 -m venv .venv
```
Windows: 
```
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependencies
```bash
pip install -r requirements.txt
```

Run (pretty-printed JSON)
```bash
python pota_stats.py --pretty
```

Subsequent runs will use the cache and are fast.
To force a fresh download:
```
python pota_stats.py --refresh
```

## Usage

```
python potastats.py [options]
```

Options


* `--pretty`
Pretty-print the results as JSON (instead of concise text output).

* `--cache <path>`
Where to store/load the cached JSON. 
Default: pota_cache/POTA_all.json

* `--refresh`
Force a fresh download even if the cache exists.

* `--max-age <hours>`
Auto-refresh when the cache is older than this many hours.
Example: --max-age 12 → refresh if cache age > 12h.

* `--url <url>`
Override the source URL (defaults to the official POTA API).

## Examples

Download (with progress), cache locally, and print a concise summary:
```
python pota_stats.py
```

Force a fresh download and overwrite the cache:
```
python pota_stats.py --refresh
```

Use cache if younger than 24 hours; otherwise auto-refresh:
```
python pota_stats.py --max-age 24 --pretty
```

Save cache to a custom path:
```
python pota_stats.py --cache /tmp/POTA_all.json --pretty
```

## Sample Output
When run with --pretty, example output looked like:
```
{
  "Total Contacts": 48081829,
  "Mode Totals": {
    "CW": 8509328,
    "Data": 9228370,
    "Phone": 30344010
  },
  "Mode Percentages": {
    "CW": 17.697596320639132,
    "Data": 19.19305107965007,
    "Phone": 63.10910094539041
  }
}
```
(Values will change over time as the live dataset updates.)

## Notes
* The dataset is large (tens of MB), so the first download can take a while.
* Caching makes subsequent runs fast.
* Only requests and tqdm are required.
