"""NATS JetStream message bus — compartido por todos los agentes."""
import asyncio
import json
import os
from typing import Callable, Any

import nats
from nats.js import JetStreamContext

NATS_URL = os.environ.get("NATS_URL", "nats://localhost:4222")


class NatsBus:
    def __init__(self):
        self._nc = None
        self._js: JetStreamContext | None = None

    async def connect(self):
        self._nc = await nats.connect(NATS_URL)
        self._js = self._nc.jetstream()

    async def close(self):
        if self._nc:
            await self._nc.drain()

    async def publish(self, subject: str, payload: dict[str, Any]):
        data = json.dumps(payload).encode()
        await self._js.publish(subject, data)

    async def subscribe(self, subject: str, handler: Callable):
        async def _cb(msg):
            data = json.loads(msg.data.decode())
            await handler(data)
            await msg.ack()

        await self._js.subscribe(subject, cb=_cb, durable=subject.replace(".", "_"))


bus = NatsBus()
