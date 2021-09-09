"""Update manifest for current release version."""
import json
import os
import sys

COMPONENT = "o365"

version = str(sys.argv[2]).replace("refs/tags/", "")
version = version[1 : len(version)]

print(f"Version to update to {version}")

manifest_file = f"{os.getcwd()}/custom_components/{COMPONENT}/manifest.json"
# manifest_file = f"{os.getcwd()}/../manifest.json"


with open(manifest_file, "r") as manifest:
    manifest_data = json.load(manifest)
    manifest_data["version"] = version

with open(manifest_file, "w") as manifest:
    json.dump(manifest_data, manifest, indent=2)
