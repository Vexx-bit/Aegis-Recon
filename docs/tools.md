
---

### `docs/tools_manifest.md`
```md
# Tools Manifest — Aegis Recon

This manifest lists external tools, how we call them, and required commands.

## Nmap
- Install: `sudo apt install nmap`
- Called in ai_services/scan_worker.py as:
  `nmap -sV -oX /tmp/scan-{target}.xml {target}`

## Sublist3r
- Git repo: https://github.com/aboul3la/Sublist3r
- Install: `pip install -r tools/Sublist3r/requirements.txt`
- Called as: `python3 tools/Sublist3r/sublist3r.py -d example.com -o /tmp/subs.txt`

## Nikto
- Git repo: https://github.com/sullo/nikto
- Called as: `perl tools/nikto/nikto.pl -h example.com -o /tmp/nikto.json -Format json`

## sqlmap
- Git repo: https://github.com/sqlmapproject/sqlmap
- Called with explicit authorization only.

## Recon-ng
- Git repo: https://github.com/lanmaster53/recon-ng
- Optional module-run usage. We mimic its modular jobs inside ai_services/jobs/.
