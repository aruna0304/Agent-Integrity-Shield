"""Download and verify official ToolEmu benchmark files.

Official Source:
- Repository: https://github.com/ryoungj/ToolEmu
- Paper: "ToolEmu: Identifying and Mitigating Risks in LLM Tool Use" (Ruan et al., 2024)
- Files:
  - all_cases.json: 144 curated test cases across 36 high-stakes toolkits
  - all_toolkits.json: specifications and emulated tool definitions
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "toolemu"

SOURCES = {
    "all_cases.json": "https://raw.githubusercontent.com/ryoungj/ToolEmu/main/assets/all_cases.json",
    "all_toolkits.json": "https://raw.githubusercontent.com/ryoungj/ToolEmu/main/assets/all_toolkits.json",
}


def download_file(url: str, dest: Path) -> str:
    """Download a file from a URL to dest path and return its sha256 hash."""
    print(f"Downloading: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    sha256 = hashlib.sha256(dest.read_bytes()).hexdigest()
    return sha256


def verify_files() -> None:
    """Verify downloaded files and print provenance metadata."""
    print("\n--- ToolEmu Acquisition & Provenance Verification ---")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    provenance_log = {}
    for filename, url in SOURCES.items():
        dest = RAW_DIR / filename
        if not dest.exists():
            sha256 = download_file(url, dest)
        else:
            sha256 = hashlib.sha256(dest.read_bytes()).hexdigest()
            print(f"Found existing: {dest.name} (SHA-256: {sha256})")
        
        # Load and inspect count
        data = json.loads(dest.read_text(encoding="utf-8"))
        count = len(data) if isinstance(data, (list, dict)) else "unknown"
        
        provenance_log[filename] = {
            "source_url": url,
            "local_path": str(dest.relative_to(PROJECT_ROOT)),
            "sha256": sha256,
            "size_bytes": dest.stat().st_size,
            "item_count": count,
        }
        print(f"  - {filename}: {count} items, {dest.stat().st_size:,} bytes")
        print(f"    Source: {url}")
        print(f"    SHA-256: {sha256}\n")

    # Write provenance record
    provenance_file = RAW_DIR / "provenance.json"
    provenance_file.write_text(json.dumps(provenance_log, indent=2), encoding="utf-8")
    print(f"Provenance metadata written to: {provenance_file.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    verify_files()
