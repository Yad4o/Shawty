"""
Git Client — Phase 3
Wraps GitPython for agent-accessible Git operations.
All operations happen on the workspace repository.
"""
from __future__ import annotations

from pathlib import Path

import git
from git import Repo, InvalidGitRepositoryError

from backend.core.logging import logger


class GitClient:
    """
    Agent-friendly Git wrapper.
    
    Provides: status, diff, commit, branch, checkout, push, log.
    Raises GitError (wraps GitPython exceptions) for clean error handling.
    """

    def __init__(self, repo_path: str) -> None:
        self.repo_path = Path(repo_path)
        self._repo: Repo | None = None

    @property
    def repo(self) -> Repo:
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path)
            except InvalidGitRepositoryError:
                raise ValueError(f"Not a Git repository: {self.repo_path}")
        return self._repo

    def init(self) -> str:
        """Initialize a new Git repo at workspace path."""
        self._repo = Repo.init(self.repo_path)
        logger.info("git_init", path=str(self.repo_path))
        return f"Initialized empty Git repository at {self.repo_path}"

    def status(self) -> str:
        """Return git status as a string."""
        return self.repo.git.status()

    def diff(self, staged: bool = False) -> str:
        """Return git diff (staged or unstaged)."""
        if staged:
            return self.repo.git.diff("--staged")
        return self.repo.git.diff()

    def add(self, paths: list[str] | str = ".") -> str:
        """Stage files for commit."""
        if isinstance(paths, str):
            paths = [paths]
        self.repo.index.add(paths)
        return f"Staged: {paths}"

    def commit(self, message: str, author_name: str = "OmClaw", author_email: str = "omclaw@local") -> str:
        """Create a commit with all staged changes."""
        author = git.Actor(author_name, author_email)
        commit = self.repo.index.commit(message, author=author, committer=author)
        logger.info("git_commit", sha=commit.hexsha[:8], message=message[:60])
        return f"Committed: {commit.hexsha[:8]} — {message}"

    def branch(self, name: str) -> str:
        """Create a new branch."""
        new_branch = self.repo.create_head(name)
        logger.info("git_branch_created", name=name)
        return f"Branch created: {name}"

    def checkout(self, branch_name: str) -> str:
        """Switch to an existing branch."""
        self.repo.git.checkout(branch_name)
        return f"Switched to branch: {branch_name}"

    def push(self, remote: str = "origin", branch: str | None = None) -> str:
        """Push to remote."""
        branch = branch or self.repo.active_branch.name
        self.repo.git.push(remote, branch)
        logger.info("git_push", remote=remote, branch=branch)
        return f"Pushed to {remote}/{branch}"

    def log(self, max_count: int = 10) -> str:
        """Return recent commit log."""
        return self.repo.git.log(f"--max-count={max_count}", "--oneline")

    def current_branch(self) -> str:
        return self.repo.active_branch.name

    def clone(self, url: str, dest: str, pat: str | None = None) -> str:
        """Clone a remote repository into dest."""
        if pat:
            # Inject PAT into HTTPS URL
            if url.startswith("https://"):
                url = url.replace("https://", f"https://{pat}@")
        Repo.clone_from(url, dest)
        logger.info("git_cloned", url=url, dest=dest)
        return f"Cloned to {dest}"
