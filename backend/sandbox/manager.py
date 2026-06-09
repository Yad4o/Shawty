"""
Docker Sandbox Manager — Phase 2
Manages isolated Docker containers for safe code execution.
The AI NEVER executes commands directly on the host.
All execution happens inside a purpose-built sandbox container.

Design decisions:
- One container per session (reused across tool calls for speed)
- Workspace mounted from host so files persist
- Non-root user inside container
- CPU + memory limits enforced
- Timeout on all exec calls
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

import docker
import docker.errors
from docker.models.containers import Container

from backend.core.config import settings
from backend.core.logging import logger


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @property
    def output(self) -> str:
        return self.stdout + ("\n" + self.stderr if self.stderr else "")


class SandboxManager:
    """
    Manages a pool of sandbox containers.
    Each session gets its own container that persists for the session lifetime.
    """

    def __init__(self) -> None:
        self._client = docker.from_env()
        self._containers: dict[str, Container] = {}  # session_id → container

    def get_or_create(self, session_id: str) -> Container:
        """Return existing container for session, or create a new one."""
        if session_id in self._containers:
            container = self._containers[session_id]
            try:
                container.reload()
                if container.status == "running":
                    return container
            except docker.errors.NotFound:
                pass  # Container gone, create a new one

        container = self._create_container(session_id)
        self._containers[session_id] = container
        return container

    def _create_container(self, session_id: str) -> Container:
        """Spin up a new sandbox container."""
        container_name = f"omclaw-sandbox-{session_id[:8]}"
        workspace_mount = {
            settings.HOST_WORKSPACE_DIR: {
                "bind": settings.DOCKER_WORKSPACE_DIR,
                "mode": "rw",
            }
        }
        logger.info("sandbox_creating", session_id=session_id[:8])
        container = self._client.containers.run(
            image=settings.DOCKER_SANDBOX_IMAGE,
            name=container_name,
            volumes=workspace_mount,
            working_dir=settings.DOCKER_WORKSPACE_DIR,
            detach=True,
            tty=True,
            mem_limit="512m",
            nano_cpus=1_000_000_000,  # 1 CPU
            network_mode="none",      # No network inside sandbox
            remove=False,
        )
        logger.info("sandbox_created", container=container_name)
        return container

    async def execute(
        self,
        session_id: str,
        command: str,
        timeout: int = 30,
        workdir: str | None = None,
    ) -> ExecResult:
        """
        Execute a shell command inside the session's sandbox container.

        Args:
            session_id: Which session's container to use.
            command: Shell command to run (runs via /bin/bash -c).
            timeout: Seconds before killing the exec.
            workdir: Working directory inside the container.

        Returns:
            ExecResult with exit_code, stdout, stderr.
        """
        container = self.get_or_create(session_id)
        wd = workdir or settings.DOCKER_WORKSPACE_DIR

        logger.info("sandbox_exec", session=session_id[:8], command=command[:80])

        def _run_exec() -> tuple[int, bytes, bytes]:
            exec_id = self._client.api.exec_create(
                container.id,
                cmd=["/bin/bash", "-c", command],
                workdir=wd,
                stdout=True,
                stderr=True,
            )
            raw = self._client.api.exec_start(exec_id["Id"], stream=False)
            inspect = self._client.api.exec_inspect(exec_id["Id"])
            return inspect["ExitCode"], raw, b""

        try:
            exit_code, stdout_raw, stderr_raw = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _run_exec),
                timeout=timeout,
            )
            return ExecResult(
                exit_code=exit_code,
                stdout=stdout_raw.decode("utf-8", errors="replace") if stdout_raw else "",
                stderr=stderr_raw.decode("utf-8", errors="replace") if stderr_raw else "",
            )
        except TimeoutError:
            logger.warning("sandbox_timeout", command=command[:60])
            return ExecResult(exit_code=124, stdout="", stderr=f"Command timed out after {timeout}s")
        except Exception as e:
            logger.error("sandbox_exec_error", error=str(e))
            return ExecResult(exit_code=1, stdout="", stderr=str(e))

    def stop_session(self, session_id: str) -> None:
        """Stop and remove the sandbox container for a session."""
        container = self._containers.pop(session_id, None)
        if container:
            try:
                container.stop(timeout=5)
                container.remove()
                logger.info("sandbox_stopped", session_id=session_id[:8])
            except Exception as e:
                logger.warning("sandbox_stop_error", error=str(e))

    def cleanup_all(self) -> None:
        """Stop all active sandbox containers. Called on shutdown."""
        for session_id in list(self._containers.keys()):
            self.stop_session(session_id)
