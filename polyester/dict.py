import queue  # The system library
import uuid
from typing import Any, List

from .async_utils import retry
from .client import Client
from .config import logger
from .object import Object, requires_create
from .proto import api_pb2


class Dict(Object):
    def __init__(self, init_data={}):
        super().__init__(args=dict(init_data=init_data))

    def _serialize_values(self, data):
        return {k: self.client.serialize(v) for k, v in data.items()}

    async def _create_or_get(self):
        serialized = self._serialize_values(self.args.init_data)
        req = api_pb2.DictCreateRequest(session_id=self.session.session_id, data=serialized)
        response = await self.client.stub.DictCreate(req)
        logger.debug("Created dict with id %s" % response.dict_id)
        return response.dict_id

    @requires_create
    async def get(self, key):
        req = api_pb2.DictGetRequest(dict_id=self.object_id, key=key)
        resp = await self.client.stub.DictGet(req)
        if not resp.found:
            raise KeyError(f"KeyError: {key} not in dict {self.object_id}")
        return self.client.deserialize(resp.value)

    @requires_create
    async def __getitem__(self, key):
        return await self.get(key)

    @requires_create
    async def update(self, **kwargs):
        serialized = self._serialize_values(kwargs)
        req = api_pb2.DictUpdateRequest(dict_id=self.object_id, updates=serialized)
        await self.client.stub.DictUpdate(req)

    @requires_create
    async def put(self, key, value):
        updates = {key: value}
        serialized = self._serialize_values(updates)
        req = api_pb2.DictUpdateRequest(dict_id=self.object_id, updates=serialized)
        await self.client.stub.DictUpdate(req)

    # NOTE: setitem only works in a synchronous context.
    @requires_create
    async def __setitem__(self, key, value):
        return await self.put(key, value)

    @requires_create
    async def pop(self, key):
        req = api_pb2.DictPopRequest(dict_id=self.object_id, key=key)
        resp = await self.client.stub.DictPop(req)
        if not resp.found:
            raise KeyError(f"KeyError: {key} not in dict {self.object_id}")
        return self.client.deserialize(resp.value)
