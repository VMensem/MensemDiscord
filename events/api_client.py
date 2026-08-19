import aiohttp
import os
import logging
import asyncio

# Используем стандартный logger
logger = logging.getLogger("bot.api_client")

class EventsAPIClient:
    def __init__(self):
        self.session = None
        self._timeout = aiohttp.ClientTimeout(total=10)

    def _get_api_key(self):
        return os.getenv("MENSEM_API_KEY")

    def _get_base_url(self):
        return os.getenv("MENSEM_EVENTS_API_URL", "http://localhost:1000/api")

    async def _get_headers(self):
        return {
            "X-API-Key": self._get_api_key(),
            "Content-Type": "application/json"
        }

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self._timeout)

    async def _request(self, method, endpoint, **kwargs):
        await self.ensure_session()
        url = f"{self._get_base_url()}{endpoint}"
        headers = await self._get_headers()
        
        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    logger.error(f"API Error {resp.status} for {method} {url}: {text}")
                    return {"status": resp.status, "data": None, "error": text}
                
                data = await resp.json()
                return {"status": resp.status, "data": data, "error": None}
        except aiohttp.ClientError as e:
            logger.error(f"Connection error for {method} {url}: {e}")
            return {"status": 500, "data": None, "error": str(e)}
        except asyncio.TimeoutError:
            logger.error(f"Timeout error for {method} {url}")
            return {"status": 504, "data": None, "error": "Timeout"}

    async def get_events(self, guild_id):
        return await self._request("GET", f"/events?guild_id={guild_id}")

    async def get_event(self, event_id, guild_id):
        # We might need to adjust API to accept guild_id in GET /events/<id> too
        return await self._request("GET", f"/events/{event_id}", params={"guild_id": guild_id})

    async def create_event(self, event_data):
        # event_data MUST contain guild_id
        return await self._request("POST", "/events", json=event_data)

    async def update_event(self, event_id, update_data):
        # update_data MUST contain guild_id
        return await self._request("POST", f"/events/{event_id}/update", json=update_data)

    async def close_event(self, event_id, guild_id):
        return await self._request("POST", f"/events/{event_id}/close", json={"guild_id": guild_id})

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

api_client = EventsAPIClient()
