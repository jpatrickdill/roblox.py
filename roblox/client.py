from cached_property import cached_property

from roblox.errors import *
from roblox.http import Session
from roblox.user import ClientUser, User, FriendRequest
from roblox.asset import Asset
from roblox.game import Place, Universe
from roblox.enums import AssetType
import re

id_re = re.compile(r"/(\d+)/")


class Roblox:
    def __init__(self):
        self.username = ""

        self._state = Session()
        self._state.client = self

    async def login(self, username=None, password=None):
        await self._state.login(username, password)

        self.username = self._state.username  # update username

    async def manual_auth(self, username, cookie):
        await self._state.manual_auth(username, cookie)

        self.username = username

    async def logged_in(self):
        return await self._state.is_authorized()

    async def logout(self):
        return await self._state.logout()

    async def close(self):
        await self._state.close()

    @cached_property
    def user(self):
        data = {"username": self.username}

        return ClientUser(state=self._state, data=data)

    me = user

    async def get_user(self, *, id=None, username=None):
        if username is None and id is None:
            raise UserIdentificationError("Must provide user ID or username")

        if username == self.username:
            return ClientUser(state=self._state, data={"username": username, "id": id})

        return User(state=self._state, data={"username": username, "id": id})

    async def get_asset(self, asset_id):
        if isinstance(asset_id, str):
            asset_id = int(id_re.search(asset_id).group(1))

        p_info = await self._state.product_info(asset_id)
        if p_info["AssetTypeId"] == AssetType.Place:
            return Place(state=self._state, data=p_info)

        return Asset(state=self._state, data=p_info)

    async def get_universe(self, universe_id, data=None):
        _data = {"id": universe_id}
        if data:
            _data.update(**data)
        return Universe(state=self._state, data=_data)

    async def blocked_users(self):
        r = []
        for blocked in (await self._state.my_settings())["BlockedUsersModel"]["BlockedUsers"]:
            r.append(User(state=self._state, data={
                "username": blocked["Name"],
                "id": blocked["uid"]
            }))

        return r

    async def get_friend_requests(self):
        async for data in self._state.get_friend_requests():
            yield FriendRequest(state=self._state, data=data)

    async def decline_all_requests(self):
        return await self._state.decline_all_friend_requests()

    async def friend_requests_count(self):
        return await self._state.friend_request_count()
