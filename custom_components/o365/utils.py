import os
import json
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup
from .const import DEFAULT_CACHE_PATH, SCOPE, CONFIG_BASE_DIR, DATETIME_FORMAT


def clean_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    body = soup.find("body")
    if body:
        return soup.find("body").get_text(" ", strip=True)
    else:
        return html


def validate_permissions(token_path=DEFAULT_CACHE_PATH, token_filename="o365.token"):
    full_token_path = os.path.join(token_path, token_filename)
    if not os.path.exists(full_token_path) or not os.path.isfile(full_token_path):
        return False
    with open(full_token_path, "r", encoding="UTF-8") as fh:
        raw = fh.read()
        permissions = json.loads(raw)["scope"]
    scope = [x for x in SCOPE if x != "offline_access"]
    return all([x in permissions for x in scope])


def get_ha_filepath(filepath):
    _filepath = Path(filepath)
    if _filepath.parts[0] == "/" and _filepath.parts[1] == "config":
        _filepath = os.path.join(CONFIG_BASE_DIR, *_filepath.parts[2:])

    if not os.path.isfile(_filepath):
        if not os.path.isfile(filepath):
            raise ValueError(f"Could not access file {filepath}")
        else:
            return filepath
    return _filepath


def zip_files(filespaths, zip_name="archive.zip"):
    if Path(zip_name).suffix != ".zip":
        zip_name += ".zip"

    with zipfile.ZipFile(zip_name, mode="w") as zf:
        for f in filespaths:
            zf.write(f, os.path.basename(f))
    return zip_name


def get_email_attributes(mail):
    return {
        "subject": mail.subject,
        "body": clean_html(mail.body),
        "received": mail.received.strftime(DATETIME_FORMAT),
        "to": [x.address for x in mail.to],
        "cc": [x.address for x in mail.cc],
        "bcc": [x.address for x in mail.bcc],
        "sender": mail.sender.address,
        "has_attachments": mail.has_attachments,
        "attachments": [x.name for x in mail.attachments],
    }
