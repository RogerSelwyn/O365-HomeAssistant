import os
import requests
import json

COMPONENT = "o365"

harequire = []
request = requests.get(
    "https://raw.githubusercontent.com/home-assistant/home-assistant/dev/setup.py"
)
request = request.text.split("REQUIRES = [")[1].split("]")[0].split("\n")
for req in request:
    if "=" in req:
        harequire.append(req.split(">")[0].split("=")[0].split('"')[1])

print(harequire)

with open(f"{os.getcwd()}/custom_components/{COMPONENT}/manifest.json", "r") as manifest:
    manifest = json.load(manifest)
    requirements = []
    for req in manifest["requirements"]:
        requirements.append(req)

for req in requirements:
    if req.split(">")[0].split("=")[0] in harequire:
        print(f"{req.split('>')[0].split('=')[0]} in HA requirements, no need here.")
print(json.dumps(manifest["requirements"], indent=4, sort_keys=True))

with open(f"{os.getcwd()}/requirements.txt", "w") as requirementsfile:
    for req in requirements:
        requirementsfile.write(req + "\n")
