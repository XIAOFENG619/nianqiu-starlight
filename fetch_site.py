"""Assemble the verified public files as a Pages artifact."""
import hashlib
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ORIGIN = "https://nianqiu-starlight-voyage.flashyhyacinth2.chatgpt.site/"
FILES = json.loads(Path("deployment.json").read_text())
OUTPUT = Path("site")

def fetch(item):
    name, expected = item
    for attempt in range(4):
        try:
            request = urllib.request.Request(ORIGIN + name, headers={"User-Agent": "starlight-pages-deploy/1.0"})
            with urllib.request.urlopen(request, timeout=55) as response:
                data = response.read()
            if name == "index.html" and hashlib.sha256(data).hexdigest() != expected:
                # Hosting may append its challenge bootstrap immediately before </body>.
                # The recovered bytes must still match the trusted release digest.
                data = re.sub(br"<script>[^<]*?\(function\(\).*?</script>(?=</body>)", b"", data, flags=re.S)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("Release checksum differs for " + name)
            output = OUTPUT / name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
            return
        except (OSError, ValueError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(fetch, FILES.items()))
print(f"Verified {len(FILES)} files")
