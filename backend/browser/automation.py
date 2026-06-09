"""
Browser Automation — Phase 7
Playwright-based browser automation for web tasks.
The agent can navigate pages, click elements, fill forms, and extract content.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from backend.core.logging import logger


class BrowserAutomation:
    """
    Managed Playwright browser session.
    
    Usage:
        async with BrowserAutomation() as browser:
            result = await browser.navigate("https://example.com")
            content = await browser.get_text("h1")
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="OmClaw/0.1 (AI Coding Agent)",
        )
        self._page = await self._context.new_page()
        logger.info("browser_started", headless=self._headless)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("browser_stopped")

    async def navigate(self, url: str, wait_for: str = "networkidle") -> str:
        """Navigate to a URL and wait for load."""
        await self._page.goto(url, wait_until=wait_for)
        title = await self._page.title()
        logger.info("browser_navigate", url=url, title=title)
        return f"Navigated to: {url} | Title: {title}"

    async def get_text(self, selector: str) -> str:
        """Get text content of a matched element."""
        element = await self._page.query_selector(selector)
        if not element:
            return f"Element not found: {selector}"
        return await element.text_content() or ""

    async def get_page_content(self) -> str:
        """Get the full page text content (no HTML tags)."""
        return await self._page.inner_text("body")

    async def click(self, selector: str) -> str:
        """Click an element."""
        await self._page.click(selector)
        return f"Clicked: {selector}"

    async def fill(self, selector: str, value: str) -> str:
        """Fill an input field."""
        await self._page.fill(selector, value)
        return f"Filled {selector} with: {value[:30]}"

    async def screenshot(self, path: str = "screenshot.png") -> str:
        """Take a screenshot and save it."""
        await self._page.screenshot(path=path, full_page=True)
        return f"Screenshot saved: {path}"

    async def evaluate(self, js: str) -> Any:
        """Execute JavaScript in the page context."""
        return await self._page.evaluate(js)

    @asynccontextmanager
    async def session(self):
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
