"""
GitHub Client — Phase 4
Wraps PyGitHub for agent-accessible GitHub operations.
Requires GITHUB_PAT in .env.
"""
from __future__ import annotations

from github import Github, GithubException
from github.Repository import Repository as GithubRepo

from backend.core.config import settings
from backend.core.logging import logger


class GitHubClient:
    """
    Agent-friendly GitHub wrapper.
    Provides: repo info, create repo, create PR, list PRs, create issue.
    """

    def __init__(self, pat: str | None = None) -> None:
        token = pat or settings.GITHUB_PAT
        if not token:
            raise ValueError("GITHUB_PAT not set. Add it to your .env file.")
        self._gh = Github(token)
        self._user = self._gh.get_user()

    def get_repo(self, owner: str, name: str) -> GithubRepo:
        return self._gh.get_repo(f"{owner}/{name}")

    def list_repos(self) -> list[str]:
        return [r.full_name for r in self._user.get_repos()]

    def create_repo(self, name: str, private: bool = False, description: str = "") -> dict:
        repo = self._user.create_repo(name, private=private, description=description)
        logger.info("github_repo_created", name=repo.full_name)
        return {"name": repo.full_name, "url": repo.clone_url, "ssh": repo.ssh_url}

    def create_pull_request(
        self,
        owner: str,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict:
        repo = self.get_repo(owner, repo_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        logger.info("github_pr_created", number=pr.number, title=title)
        return {"number": pr.number, "url": pr.html_url, "title": pr.title}

    def create_issue(self, owner: str, repo_name: str, title: str, body: str = "") -> dict:
        repo = self.get_repo(owner, repo_name)
        issue = repo.create_issue(title=title, body=body)
        return {"number": issue.number, "url": issue.html_url}

    def get_file_contents(self, owner: str, repo_name: str, path: str, ref: str = "main") -> str:
        repo = self.get_repo(owner, repo_name)
        contents = repo.get_contents(path, ref=ref)
        return contents.decoded_content.decode("utf-8")
