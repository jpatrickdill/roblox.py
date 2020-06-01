from __future__ import annotations

import re
from typing import Union

from cached_property import cached_property

from roblox.asset import Asset
from roblox.enums import AssetType
from roblox.errors import *
from roblox.game import Place, Universe
from roblox.group import Group
from roblox.http import Session
from roblox.iterables import AsyncIterator
from roblox.user import ClientUser, User, FriendRequest

id_re = re.compile(r"/(\d+)/")


class Roblox:
    """
    Represents the connection to the Roblox API.
    This object is used to authorize with Roblox, as well as fetch personal data and specific users, assets,
    groups, and games.
    """

    def __init__(self):
        self.username = ""

        self._state = Session()
        self._state.client = self

    async def login(self, username: str, password: str):
        """|coro|

        Attempts to authorize using a username and password.

        Args:
            username: Username to authorize with.
            password: Password to authorize with.
        """

        await self._state.login(username, password)

        self.username = self._state.username  # update username
        await self.user._get_profile_data()  # necessary for equality checks

    async def manual_auth(self, username: str, security_token: str):
        """|coro|

        Authorizes the user using a .ROBLOSECURITY cookie.

        Args:
            username: Username the token belongs to.
            security_token: Token to authorize with.
        """

        await self._state.manual_auth(username, security_token)

        self.username = username
        await self.user._get_profile_data()  # necessary for equality checks

    async def logged_in(self) -> bool:
        """|coro|

        Checks that the client is authorized with Roblox.

        :rtype: bool
        """

        return await self._state.is_authorized()

    async def logout(self):
        """|coro|

        Logs out of the authorized user.
        """

        return await self._state.logout()

    async def close(self):
        await self._state.close()

    @cached_property
    def user(self) -> ClientUser:
        """
        :class:`.ClientUser` representing the authorized user.
        """

        data = {"username": self.username}
        return ClientUser(state=self._state, data=data)

    async def get_user(self, *, id: int = None, username: str = None) -> Union[User, ClientUser]:
        """|coro|

        Creates a :class:`User` object given a user ID or username.
        Arguments must be set explicitly.

        Args:
            id: User's ID
            username: User's username

        :rtype: :class:`.User` | :class:`.ClientUser`
        """

        if username is None and id is None:
            raise UserIdentificationError("Must provide user ID or username")

        if username == self.username:
            return ClientUser(state=self._state, data={"username": username, "id": id})

        return User(state=self._state, data={"username": username, "id": id})

    async def get_asset(self, asset_id) -> Union[Asset, Place]:
        """|coro|

        Creates a :class:`Asset` or :class:`Place` object given an Asset ID.

        Args:
            asset_id: Asset's ID

        :rtype: :class:`.Asset` | :class:`Place`
        """

        if isinstance(asset_id, str):
            asset_id = int(id_re.search(asset_id).group(1))

        p_info = await self._state.product_info(asset_id)
        if p_info["AssetTypeId"] == AssetType.Place:
            return Place(state=self._state, data=p_info)

        return Asset(state=self._state, data=p_info)

    async def get_universe(self, universe_id, *, data=None) -> Universe:
        """|coro|

        Creates a :class:`Universe` object given a Universe/Game ID.

        Args:
            universe_id: Universe/Game ID.

        :rtype: :class:`.Universe`
        """

        _data = {"id": universe_id}
        if data:
            _data.update(**data)
        return Universe(state=self._state, data=_data)

    async def get_group(self, group_id, *, data=None) -> Group:
        """|coro|

        Creates a :class:`Group` object given a Group ID.

        Args:
            group_id: Group ID.

        :rtype: :class:`.Group`
        """

        _data = {"id": group_id}
        if data:
            _data.update(**data)
        return Group(state=self._state, data=_data)

    @property
    def blocked(self) -> AsyncIterator:
        """
        :class:`.AsyncIterator` for the client's blocked users.

        Yields:
            :class:`User`
        """
        async def gen():
            for blocked in (await self._state.my_settings())["BlockedUsersModel"]["BlockedUsers"]:
                yield User(state=self._state, data={
                    "username": blocked["Name"],
                    "id": blocked["uid"]
                })

        return AsyncIterator(gen=gen)

    @property
    def friend_requests(self) -> _FriendRequests:
        """
        :class:`.AsyncIterator` for the client's friend requests.

        **Additional Methods**

        *await* ``client.friend_requests.decline_all()``

        - Declines all friend requests.

        Yields:
            :class:`.FriendRequest`
        """

        return _FriendRequests(state=self._state)


class _FriendRequests(AsyncIterator):
    async def __aiter__(self):
        async for data in self._state.get_friend_requests():
            yield FriendRequest(state=self._state, data=data)

    async def count(self):
        return await self._state.friend_request_count()

    async def decline_all(self):
        return await self._state.decline_all_friend_requests()
