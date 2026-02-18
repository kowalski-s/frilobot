"""Парсер каналов Telegram — поиск через DuckDuckGo (основной) и tgstat.com (резерв)."""

import asyncio
import logging
import re

import cloudscraper
from bs4 import BeautifulSoup, Tag
from ddgs import DDGS

logger = logging.getLogger(__name__)

_TGSTAT_URL = "https://tgstat.com/channels/search"


class TgstatParser:
    """Парсит Telegram-каналы: DuckDuckGo site:t.me + tgstat.com AJAX."""

    def __init__(self) -> None:
        self._scraper: cloudscraper.CloudScraper | None = None
        self._csrf_token: str | None = None

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        """Ищет каналы по запросу. Возвращает список словарей с данными каналов.

        Возвращает пустой список при любой ошибке.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._search_sync, query, limit)
        except Exception as e:
            logger.warning("Channel search error: %s", e)
            return []

    def _search_sync(self, query: str, limit: int) -> list[dict]:
        """Синхронный поиск: сначала DuckDuckGo, при неудаче — tgstat."""
        results = self._search_ddg(query, limit)
        if results:
            return results

        logger.info("DDG returned no results, trying tgstat")
        return self._search_tgstat(query, limit)

    # ==================== DuckDuckGo ====================

    def _search_ddg(self, query: str, limit: int) -> list[dict]:
        """Поиск каналов через DuckDuckGo site:t.me."""
        search_query = f"site:t.me {query}"
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(search_query, max_results=limit * 3))
        except Exception as e:
            logger.warning("DDG search error: %s", e)
            return []

        if not raw_results:
            return []

        seen: set[str] = set()
        channels: list[dict] = []

        for item in raw_results:
            channel = self._parse_ddg_result(item)
            if not channel:
                continue
            username = channel["username"]
            if username in seen:
                continue
            seen.add(username)
            channels.append(channel)
            if len(channels) >= limit:
                break

        logger.info("DDG search: found %d unique channels", len(channels))
        return channels

    @staticmethod
    def _parse_ddg_result(item: dict) -> dict | None:
        """Извлекает данные канала из результата DuckDuckGo."""
        try:
            href = item.get("href", "")
            title = item.get("title", "")
            body = item.get("body", "")

            # Извлекаем username из URL: t.me/username или t.me/s/username
            match = re.search(r"t\.me/(?:s/)?([a-zA-Z]\w{3,})", href)
            if not match:
                return None

            username = match.group(1)

            # Пропускаем служебные страницы
            if username.lower() in ("s", "addstickers", "joinchat", "addtheme", "proxy"):
                return None

            # Очищаем заголовок от "Telegram: Contact/View @..."
            clean_title = re.sub(
                r"^Telegram:\s*(Contact|View|Join)\s*@\S+\s*[-–—]?\s*",
                "",
                title,
            ).strip()
            # Убираем " - Telegram" в конце
            clean_title = re.sub(r"\s*[-–—]\s*Telegram\s*$", "", clean_title).strip()
            if not clean_title:
                clean_title = f"@{username}"

            return {
                "username": username,
                "title": clean_title,
                "description": body[:500] if body else None,
                "subscribers_count": None,
                "category": None,
            }
        except Exception as e:
            logger.debug("DDG: error parsing result: %s", e)
            return None

    # ==================== tgstat.com ====================

    def _get_scraper(self) -> cloudscraper.CloudScraper:
        """Ленивая инициализация cloudscraper."""
        if self._scraper is None:
            self._scraper = cloudscraper.create_scraper()
        return self._scraper

    def _ensure_tgstat_session(self) -> None:
        """Получает CSRF-токен и cookies для tgstat.com."""
        if self._csrf_token:
            return
        try:
            scraper = self._get_scraper()
            resp = scraper.get(_TGSTAT_URL, timeout=15)
            if resp.status_code != 200:
                return
            soup = BeautifulSoup(resp.text, "html.parser")
            meta = soup.select_one("meta[name=csrf-token]")
            if meta:
                self._csrf_token = meta.get("content", "")
        except Exception as e:
            logger.warning("tgstat: session init error: %s", e)

    def _search_tgstat(self, query: str, limit: int) -> list[dict]:
        """Поиск через tgstat.com AJAX API."""
        self._ensure_tgstat_session()
        scraper = self._get_scraper()

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": _TGSTAT_URL,
        }
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        try:
            resp = scraper.post(
                _TGSTAT_URL,
                data={"q": query},
                headers=headers,
                timeout=15,
            )
        except Exception as e:
            logger.warning("tgstat: request error: %s", e)
            return []

        if resp.status_code != 200:
            self._csrf_token = None
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        if data.get("status") == "restricted":
            logger.warning("tgstat: rate limited")
            self._csrf_token = None
            self._scraper = None
            return []

        html = data.get("html", "")
        if not html:
            return []

        return self._parse_tgstat_html(html, limit)

    def _parse_tgstat_html(self, html: str, limit: int) -> list[dict]:
        """Извлекает данные каналов из HTML ответа tgstat AJAX."""
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".peer-item-row")
        if not cards:
            return []

        results: list[dict] = []
        for card in cards[:limit]:
            channel = self._parse_tgstat_card(card)
            if channel and channel.get("username"):
                results.append(channel)

        logger.info("tgstat search: found %d channels", len(results))
        return results

    def _parse_tgstat_card(self, card: Tag) -> dict | None:
        """Извлекает данные канала из карточки tgstat."""
        try:
            data: dict = {
                "username": None,
                "title": None,
                "description": None,
                "subscribers_count": None,
                "category": None,
            }

            link = card.select_one("a[href*='/channel/@']")
            if link:
                href = str(link.get("href", ""))
                for part in href.split("/"):
                    if part.startswith("@"):
                        data["username"] = part.lstrip("@")
                        break

            title_el = card.select_one(".font-16.text-dark")
            if title_el:
                data["title"] = title_el.get_text(strip=True)

            subs_el = card.select_one(".font-14.text-dark")
            if subs_el:
                subs_text = subs_el.get_text(strip=True)
                digits = re.sub(r"[^\d\s]", "", subs_text).replace(" ", "")
                if digits:
                    try:
                        data["subscribers_count"] = int(digits)
                    except ValueError:
                        pass

            cat_el = card.select_one(".font-12.text-dark span")
            if cat_el:
                data["category"] = cat_el.get_text(strip=True)

            return data
        except Exception as e:
            logger.debug("tgstat: error parsing card: %s", e)
            return None
