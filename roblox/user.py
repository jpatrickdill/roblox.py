import logging

import maya
from async_property import async_property, async_cached_property
from cached_property import cached_property

from roblox.abc import User as _User
from roblox.errors import *
from roblox.http import Session
from roblox.inventory import Inventory

_BaseUser = _User

log = logging.getLogger(__name__)


class BaseUser:  # _BaseUser):
    __slots__ = ("_data", "_state")

    def __init__(self, *, state: Session, data):
        self._state = state
        self._data = {
            "username": None,
            "name": None,
            "id": None,
            "created": None,
            "description": None,
            "status": None,
            "isBanned": None
        }

        for name in self.__slots__:
            if not hasattr(self, name):
                setattr(self, name, None)

        self._update(data)

        if self._data["username"] is None and self._data["id"] is None:
            raise UserIdentificationError("Username or Id must be specified in user data")

    # def __str__(self):
    #     return self._data["username"] or str(self._data["id"] or "")

    def __repr__(self):
        return "User({!r})".format(self._data["username"] or self._data["id"])

    def __hash__(self):
        return self._data["id"] or -2

    def __eq__(self, other):
        if not isinstance(other, BaseUser):
            return False

        return (self._data["id"] == other._data["id"] and self._data["id"] is not None) or \
               (self._data["username"] is not None and other._data["username"] is not None and
                self._data["username"].lower() == other._data["username"].lower()
                )

    def _update(self, data):
        data.setdefault("username", data.get("name"))
        data.setdefault("username", data.get("displayName"))

        self._data.update(data)

    async def _get_profile_data(self):
        new = await self._state.get_user_data(await self.id)
        self._update(new)

    @async_cached_property
    async def id(self):
        if self._data["id"] is None:
            new = await self._state.get_by_username(self._data["username"])
            self._update(new)

        return self._data["id"]

    @async_cached_property
    async def username(self):
        if self._data["username"] is None:
            await self._get_profile_data()

        return self._data["username"] or self._data["name"]

    @async_cached_property
    async def url(self):
        return "https://www.roblox.com/users/{}/profile".format(await self.id)

    @async_cached_property
    async def created_at(self):
        if self._data["created"] is None:
            await self._get_profile_data()

        try:
            return maya.parse(self._data["created"]).datetime()
        except OSError:
            return None

    @async_property
    async def description(self):
        if self._data["description"] is None:
            await self._get_profile_data()

        return self._data["description"]

    @async_property
    async def status(self):
        if self._data["status"] is None:
            self._update(await self._state.user_status(await self.id))

        return self._data["status"]

    @async_property
    async def is_banned(self):
        if self._data["isBanned"] is None:
            await self._get_profile_data()

        return self._data["isBanned"]

    @async_property
    async def is_premium(self):
        return await self._state.is_premium(await self.id)

    @async_property
    async def friends_iter(self):
        data = await self._state.get_user_friends(await self.id)
        return [User(state=self._state, data=friend) for friend in data]

    async def friends(self):
        for friend in await self.friends_iter():
            yield friend

    async def is_friends(self, other=None):
        if self == other or not isinstance(other, BaseUser):
            return False

        if other:  # can't use API endpoint on user other than client
            await other._get_profile_data()
            return other in await self.friends_iter

        other = other or self._state.client.user

        statuses = await self._state.check_status(await other.id, await self.id)

        return statuses[0]["status"] == "Friends"

    @property
    def followers(self):
        return FollowerList(state=self._state, user=self)

    @property
    def followings(self):
        return FollowingList(state=self._state, user=self)

    following = followings

    @cached_property
    def inventory(self):
        return Inventory(state=self._state, user=self)

    async def games(self, access_filter=None):
        async for data in self._state.get_user_games(await self.id,
                                                     access_filter=str(access_filter) if access_filter else None):
            yield await self._state.client.get_universe(data["id"], data)

    @async_property
    async def robux(self):
        return (await self._state.get_currency(await self.id))["robux"]


class FollowerList:
    __slots__ = ("_state", "user")

    def __init__(self, *, state, user):
        self._state = state
        self.user = user

    async def __aiter__(self):
        async for follower_data in self._state.followers(await self.user.id):
            yield User(state=self._state, data=follower_data)

    @async_property
    async def count(self):
        return await self._state.follower_count(await self.user.id)

    async def contains(self, other):
        async for user in self:
            if await user.id == await other.id:
                return True

        return False


class FollowingList:
    __slots__ = ("_state", "user")

    def __init__(self, *, state, user):
        self._state = state
        self.user = user

    async def __aiter__(self):
        async for following_data in self._state.followings(await self.user.id):
            yield User(state=self._state, data=following_data)

    @async_property
    async def count(self):
        return await self._state.followings_count(await self.user.id)

    async def contains(self, other):
        async for user in self:
            if await user.id == await other.id:
                return True

        return False


class ClientUser(BaseUser):
    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __repr__(self):
        return "ClientUser" + BaseUser.__repr__(self)[4:]

    def __hash__(self):
        return self._data["id"] or -2

    async def set_status(self, status):
        data = await self._state.post_status(await self.id, status)

        self._update(data)
        return data["status"]


class User(BaseUser):
    """Represents user other than the Client."""

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __hash__(self):
        return self._data["id"] or -2

    async def unfriend(self):
        await self._state.unfriend(await self.id)
        log.debug("unfriended {}".format(self))

    async def follow(self):
        await self._state.follow(await self.id)
        log.debug("followed {}".format(self))

    async def unfollow(self):
        await self._state.unfollow(await self.id)
        log.debug("unfollowed {}".format(self))

    async def request_friendship(self):
        return await self._state.request_friendship(await self.id)


class FriendRequest(User):
    """Represents a user requesting friendship with the client. This class is used to provide accept/decline methods
    while still allowing you to get user data.

    Inherits from :class:`User`"""

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __repr__(self):
        return "FriendRequest({!r})".format(self._data["username"] or self._data["id"])

    async def accept(self):
        """Accepts friend request."""

        return await self._state.accept_friend_request(await self.id)

    request_friendship = accept

    async def decline(self):
        """Declines friend request."""

        return await self._state.decline_friend_request(await self.id)
