#!/usr/bin/env python3
import json
import logging
import sys
from typing import cast

import gitlab
from jira import JIRA
from jira.client import ResultList
from jira2gitlab_config import *
from jira2gitlab_secrets import *
from rich.console import Console
from rich.logging import RichHandler

loggingConsole = Console(stderr=True)
loggingHandler = RichHandler(console=loggingConsole)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[loggingHandler]
)
log = logging.getLogger("rich")


def get_gitlab_issues(project_name: str) -> set[str]:
    log.info("Connecting to Gitlab...")
    gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN, keep_base_url=True)
    log.info("  ok")

    log.info(f"Get project {project_name}...")
    project = gl.projects.get(f"vnk-erillissovellukset/{project_name}")
    log.info("  ok")

    issues = None
    titles = set()
    page = 1
    with loggingConsole.status("Get issues...") as status:
        while True:
            issues = project.issues.list(page=page, per_page=JIRA_PAGINATION_SIZE)
            for i in issues:
                short_title = (
                    i.title.split(" ")[0].strip().replace("[", "").replace("]", "")
                )
                status.update(f"Get issues... {short_title}")
                log.info(f"{short_title}: {i.title}")
                titles.add(short_title)
            if not len(issues):
                break
            page += 1
        log.info("  ok")

    return titles


def get_jira_issues(project_name: str) -> set[str]:
    jira_server = JIRA(server=JIRA_URL, auth=JIRA_ACCOUNT)
    start_at = 0
    description = f"Loading Jira issues from project {project_name}..."
    result_list = jira_server.search_issues(
        jql_str=f"project={project_name} ORDER BY key",
        startAt=start_at,
        maxResults=1,
        validate_query=False,
    )
    total = cast(ResultList, result_list).total
    jira_issues = []
    with loggingConsole.status(f"{description} 0/{total}") as status:
        while True:
            jira_issues_batch = jira_server.search_issues(
                jql_str=f"project={project_name} ORDER BY key",
                startAt=start_at,
                maxResults=JIRA_PAGINATION_SIZE,
                validate_query=False,
                fields="[key,title]",
            )
            if not jira_issues_batch:
                break

            start_at = start_at + len(jira_issues_batch)
            jira_issues.extend(jira_issues_batch)
            status.update(
                status=f"{description} {len(jira_issues)}/{total}",
            )
            for x in jira_issues_batch:
                log.info(x)
    titles = set()
    for i in jira_issues:
        titles.add(i.key)
    return titles


if __name__ == "__main__":
    if len(PROJECTS) != 1:
        if not len(PROJECTS):
            specifier = ""
        else:
            specifier = "only "
        log.fatal(f"Please enable {specifier}one project in './jira2gitlab_config.py'.")
        log.fatal(f"You have {list(PROJECTS.keys()) if specifier else 'none'}")
        sys.exit(1)
    project = list(PROJECTS.keys())[0]
    log.info("Get issues from Gitlab")
    gitlab_issues = get_gitlab_issues(project.lower())
    log.info("Get issues from Jira")
    jira_issues = get_jira_issues(project)
    log.info("Done. Calculate differences:")
    diff = list(jira_issues - gitlab_issues)
    log.info(f"Amount of issues in Jira but not in Gitlab = {len(diff)}")
    of_name = "only-in-jira.json"
    with open(of_name, "w") as output_file:
        json.dump(diff, output_file, ensure_ascii=False, indent=2)
        log.info(f"Orphan Jira issue keys written to '{of_name}'")
