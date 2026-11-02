#!/usr/bin/env python3
"""Fetch the Islamic date from the jamiat.org.za sidebar widget and write hijri.json."""
import datetime, difflib, html, json, os, re, sys, urllib.request

URL = "https://jamiat.org.za/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hijri.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
MONTHS = ["Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani", "Jumada al-Ula",
          "Jumada al-Akhirah", "Rajab", "Shaban", "Ramadan", "Shawwal",
          "Dhu al-Qadah", "Dhu al-Hijjah"]
ALIASES = {
    "rabiulawwal": 2, "rabiulawal": 2, "rabialawal": 2, "rabii": 2,
    "rabiulakhir": 3, "rabialakhir": 3, "rabiuthani": 3, "rabiussani": 3, "rabiii": 3,
    "jumadalula": 4, "jumadaulula": 4, "jamadiulawwal": 4, "jumadaalawwal": 4, "jumadai": 4, "jumadaula": 4,
    "jumadaalukhra": 5, "jumadaalthani": 5, "jumadaalakhira": 5, "jamadiulakhir": 5, "jumadaii": 5, "jumadalakhirah": 5,
    "shaaban": 7, "ramadhan": 8, "ramazan": 8, "shawaal": 9,
    "dhulqadah": 10, "zulqadah": 10, "dhualqidah": 10, "dhulqidah": 10, "zilqad": 10,
    "dhulhijjah": 11, "zulhijjah": 11, "dhualhijja": 11, "zilhajj": 11,
}
def key(s): return re.sub(r"[^a-z]", "", s.lower())

def month_index(name):
    k = key(name)
    canon = {key(m): i for i, m in enumerate(MONTHS)}
    if k in canon: return canon[k]
    if k in ALIASES: return ALIASES[k]
    m = difflib.get_close_matches(k, list(canon) + list(ALIASES), n=1, cutoff=0.75)
    if m: return canon.get(m[0], ALIASES.get(m[0]))
    return None

def text_of(cls, page):
    m = re.search(r'class="[^"]*\b' + cls + r'\b[^"]*"[^>]*>(.*?)</', page, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else None

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "text/html"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    gd, hd = text_of("gd-out", page), text_of("hd-out", page)
    attrs = {k: re.search(r'data-site-' + k + r'="(\d+)"', page) for k in "ymd"}
    if all(attrs.values()):
        greg = datetime.date(int(attrs["y"].group(1)), int(attrs["m"].group(1)), int(attrs["d"].group(1)))
    elif gd:
        greg = datetime.datetime.strptime(gd, "%d %B %Y").date()
    else:
        sys.exit("Could not find the Gregorian date")
    m = re.match(r"^\s*(\d{1,2})\s+(.+?)\s+(\d{4})\s*(?:AH)?\s*$", hd or "")
    if not m: sys.exit("Could not parse the Islamic date: %r" % hd)
    day, mon_raw, year = int(m.group(1)), m.group(2), int(m.group(3))
    idx = month_index(mon_raw)
    if idx is None or not (1 <= day <= 30) or not (1400 <= year <= 1600):
        sys.exit("Unexpected Islamic date: %r" % hd)
    data = {"gregorian": greg.isoformat(), "hijri": "%d %s %d" % (day, MONTHS[idx], year),
            "day": day, "month": MONTHS[idx], "monthIndex": idx + 1, "year": year,
            "raw": hd, "source": "jamiat.org.za",
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()}
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {}
    core = lambda d: {k: v for k, v in d.items() if k != "fetchedAt"}
    if core(old) == core(data):
        print("No change:", data["hijri"]); return
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2); f.write("\n")
    print("Updated:", json.dumps(data))

if __name__ == "__main__":
    main()
