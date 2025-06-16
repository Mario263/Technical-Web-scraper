#!/usr/bin/env python3

import os
import json
import pandas as pd
from pathlib import Path

# Define the directories
root_dir = Path("/Users/mario/Desktop/technical-content-scraper-production")
output_dirs = [
    root_dir / "output",
    root_dir / "src" / "scrapers" / "output"
]

# List to hold all rows
rows = []

# Loop through both directories
for output_dir in output_dirs:
    if not output_dir.exists():
        print(f"⚠️ Skipping missing directory: {output_dir}")
        continue

    for file in output_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                team_id = data.get("team_id", "unknown")

                for item in data.get("items", []):
                    rows.append({
                        "name": file.name,
                        "scraped_from": team_id,
                        "url": item.get("source_url", ""),
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "author": item.get("author", "")
                    })
        except Exception as e:
            print(f"❌ Failed to read {file.name}: {e}")

# Convert to DataFrame
df = pd.DataFrame(rows)

# Save to CSV
csv_path = root_dir / "scraped_summary.csv"
df.to_csv(csv_path, index=False)
print(f"\n✅ Saved combined CSV to: {csv_path}")