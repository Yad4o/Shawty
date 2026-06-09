"""
Self-Healing Coding Loop — Phase 8
Implements the autonomous error-fix-retry cycle.

Loop:
  1. Write code
  2. Execute in Docker sandbox
  3. If error → analyze traceback → patch code → retry
  4. Stop when: success | max_retries reached | agent gives up

Design decisions:
- Max 5 retries (configurable)
- Full error context injected back to LLM on each retry
- Each retry also stores the (error, fix) pair in memory for learning
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.logging import logger
from backend.llm.client import OllamaClient
from backend.sandbox.manager import SandboxManager, ExecResult


HEAL_SYSTEM_PROMPT = """\
You are OmClaw's self-healing code repair agent.

You will be given:
1. The code that was executed
2. The error / traceback it produced
3. The original task description

Your job: analyze the error and output ONLY the corrected, complete file content.
Do not explain. Do not use markdown fences. Output raw code only.
"""


@dataclass
class HealResult:
    success: bool
    final_output: str
    attempts: int
    errors: list[str] = field(default_factory=list)


class SelfHealingLoop:
    """
    Autonomous write → run → fix → retry loop.
    
    Usage:
        healer = SelfHealingLoop(llm, sandbox)
        result = await healer.run(
            task="Write a Python script that fetches GitHub stars",
            file_path="fetch_stars.py",
            session_id="abc123",
        )
    """

    def __init__(
        self,
        llm: OllamaClient,
        sandbox: SandboxManager,
        max_retries: int = 5,
    ) -> None:
        self.llm = llm
        self.sandbox = sandbox
        self.max_retries = max_retries

    async def run(
        self,
        task: str,
        file_path: str,
        session_id: str,
        initial_code: str | None = None,
    ) -> HealResult:
        """
        Run the self-healing loop for a coding task.
        
        Args:
            task: Description of what the code should do.
            file_path: Path to the file to write/fix inside the workspace.
            session_id: Sandbox session to execute in.
            initial_code: Optional starting code (if already written by agent).
        """
        code = initial_code
        errors: list[str] = []

        for attempt in range(1, self.max_retries + 1):
            logger.info("self_heal_attempt", attempt=attempt, file=file_path)

            if code is None:
                # Generate initial code
                code = await self._generate_code(task)

            # Write code to sandbox
            write_result = await self.sandbox.execute(
                session_id=session_id,
                command=f"cat > {file_path} << 'OMCLAW_EOF'\n{code}\nOMCLAW_EOF",
            )

            # Execute code
            exec_result = await self.sandbox.execute(
                session_id=session_id,
                command=f"python {file_path}",
            )

            if exec_result.success:
                logger.info("self_heal_success", attempt=attempt)
                return HealResult(
                    success=True,
                    final_output=exec_result.output,
                    attempts=attempt,
                    errors=errors,
                )

            # Capture error
            error = exec_result.stderr or exec_result.stdout
            errors.append(error)
            logger.warning("self_heal_error", attempt=attempt, error=error[:200])

            # Ask LLM to fix
            code = await self._fix_code(task=task, broken_code=code, error=error)

        logger.error("self_heal_exhausted", max_retries=self.max_retries)
        return HealResult(
            success=False,
            final_output="",
            attempts=self.max_retries,
            errors=errors,
        )

    async def _generate_code(self, task: str) -> str:
        """Generate initial code for a task."""
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": "Output ONLY raw Python code. No markdown. No explanation."},
                {"role": "user", "content": f"Write Python code to: {task}"},
            ]
        )
        return response["message"]["content"]

    async def _fix_code(self, task: str, broken_code: str, error: str) -> str:
        """Ask the LLM to fix broken code given the error."""
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": HEAL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}\n\n"
                        f"Broken code:\n{broken_code}\n\n"
                        f"Error:\n{error}\n\n"
                        "Output the corrected complete code:"
                    ),
                },
            ]
        )
        return response["message"]["content"]
