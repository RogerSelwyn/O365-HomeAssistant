"""Create the release notes."""
import re
import sys

from github import Github

REPOSITORY = "O365-HomeAssistant"

BODY = """[![Downloads for this release](https://img.shields.io/github/downloads/rogerselwyn/{repository}/{version}/total.svg)](https://github.com/rogerselwyn/{repository}/releases/{version})

{changes}

"""

CHANGES = """
### Enhancements
### Fixes
### Maintenance

{repo_changes}

"""

CHANGE = "- [{line}]({link}) - @{author}\n"
NOCHANGE = "_No changes in this release._"

GITHUB = Github(sys.argv[2])


def _new_commits(repo, sha):
    """Get new commits in repo."""
    from datetime import datetime

    dateformat = "%a, %d %b %Y %H:%M:%S GMT"
    release_commit = repo.get_commit(sha)
    since = datetime.strptime(release_commit.last_modified, dateformat)
    commits = repo.get_commits(since=since)
    if len(list(commits)) == 1:
        return False
    return reversed(list(commits)[:-1])


def _last_repo_release(github, skip=True):
    """Return last release."""
    repo = github.get_repo(f"rogerselwyn/{REPOSITORY}")
    tag_sha = None
    data = {}
    tags = list(repo.get_tags())
    reg = "(v|^)?(\\d+\\.)?(\\d+\\.)?(\\*|\\d+)$"
    if tags:
        for tag in tags:
            tag_name = tag.name
            if re.match(reg, tag_name):
                tag_sha = tag.commit.sha
                if skip:
                    skip = False
                    continue
                break
    data["tag_name"] = tag_name
    data["tag_sha"] = tag_sha
    return data


def _get_repo_commits(github, skip=True):
    changes = ""
    repo = github.get_repo(f"rogerselwyn/{REPOSITORY}")
    commits = _new_commits(repo, _last_repo_release(github, skip)["tag_sha"])

    if not commits:
        changes = NOCHANGE
    else:
        for commit in commits:
            msg = repo.get_git_commit(commit.sha).message
            if "Merge branch " in msg:
                continue
            if "Merge pull request " in msg:
                continue
            if "\n" in msg:
                msg = msg.split("\n")[0]
            author = commit.author.login if commit.author else None
            changes += CHANGE.format(line=msg, link=commit.html_url, author=author)

    return changes


# Update release notes:
UPDATERELEASE = str(sys.argv[4])
REPO = GITHUB.get_repo(f"rogerselwyn/{REPOSITORY}")
if UPDATERELEASE == "yes":
    VERSION = str(sys.argv[6]).replace("refs/tags/", "")
    RELEASE = REPO.get_release(VERSION)
    RELEASE.update_release(
        name=VERSION,
        message=BODY.format(
            version=VERSION,
            changes=CHANGES.format(
                repo_changes=_get_repo_commits(GITHUB),
            ),
            repository=REPOSITORY,
        ),
        prerelease=True,
    )
else:
    repo_changes = _get_repo_commits(GITHUB, False)
    if repo_changes != NOCHANGE:
        VERSION = _last_repo_release(GITHUB, False)["tag_name"]
        VERSION = f"{VERSION[:-1]}{int(VERSION[-1])+1}"
        REPO.create_issue(
            title=f"Create release {VERSION}?",
            labels=["New release"],
            assignee="rogerselwyn",
            body=CHANGES.format(
                repo_changes=repo_changes,
            ),
        )
    else:
        print("Not enough changes for a release.")
