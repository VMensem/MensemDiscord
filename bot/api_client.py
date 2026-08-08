import aiohttp
import logging

class MensemAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def get_event_data(self, event_id):
        """Получение данных о событии с сайта"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/events/{event_id}", headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def post_member_status(self, user_id, status):
        """Отправка статуса участника на сайт"""
        async with aiohttp.ClientSession() as session:
            payload = {"user_id": user_id, "status": status}
            async with session.post(f"{self.base_url}/update-status", json=payload, headers=self.headers) as response:
                return response.status == 200