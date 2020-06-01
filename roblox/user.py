from __future__ import annotations
import logging

import maya
from CaseInsensitiveDict import CaseInsensitiveDict
from async_property import async_property, async_cached_property
from cached_property import cached_property

from roblox.abc import User as _BaseUser
from roblox.abc import ClientUser as _ClientUser
from roblox.abc import OtherUser as _User
from roblox.errors import *
from roblox.http import Session
from roblox.iterables import AsyncIterator
from roblox.inventory import Inventory

log = logging.getLogger(__name__)


class BaseUser(_BaseUser):  # _BaseUser):
    __slots__ = ("_data", "_state")

    def __init__(self, *, state: Session, data):
        self._state = state
        self._data = CaseInsensitiveDict({
            "username": None,
            "name": None,
            "id": None,
            "created": None,
            "description": None,
            "status": None,
            "isBanned": None
        })
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

        if self._data["id"] == other._data["id"] and self._data["id"] is not None:
            return True
        elif (self._data["username"] is not None) and (other._data["username"] is not None):
            return self._data["username"].lower() == other._data["username"].lower()
        else:
            return False

    def _update(self, data):
        data["username"] = data.get("username", data.get("name", data.get("displayname", data.get("displayName"))))
        data["id"] = data.get("id", data.get("userid", data.get("userId")))

        self._data.update(data)

    async def _get_profile_data(self):
        new = await self._state.get_user_data(await self.id)
        self._update(new)

    @async_cached_property
    async def id(self):
        """|asyncprop|

        The user's ID.

        :rtype: int
        """

        if self._data["id"] is None:
            new = await self._state.get_by_username(self._data["username"])
            self._update(new)

        return self._data["id"]

    @async_cached_property
    async def username(self):
        """|asyncprop|

        The user's username.

        :rtype: str
        """

        if self._data["username"] is None:
            await self._get_profile_data()

        return self._data["username"] or self._data["name"]

    @async_cached_property
    async def url(self):
        """|asyncprop|

        The user's profile URL.

        :rtype: str
        """

        return "https://www.roblox.com/users/{}/profile".format(await self.id)

    @async_property
    async def description(self):
        """|asyncprop|

        The user's profile description.

        :rtype: str
        """

        if self._data["description"] is None:
            await self._get_profile_data()

        return self._data["description"]

    async def status(self):
        """|coro|

        The user's current status message.

        :rtype: str
        """

        self._update(await self._state.user_status(await self.id))

        return self._data["status"]

    @async_cached_property
    async def created_at(self):
        """|asyncprop|

        :class:`datetime.datetime` at which the user was created.
        """

        if self._data["created"] is None:
            await self._get_profile_data()

        try:
            return maya.parse(self._data["created"]).datetime()
        except OSError:
            return None

    @async_property
    async def is_banned(self):
        """|asyncprop|

        Whether the user is currently banned.

        :rtype: bool
        """

        if self._data["isBanned"] is None:
            await self._get_profile_data()

        return self._data["isBanned"]

    @async_property
    async def is_premium(self):
        """|asyncprop|

        Whether the user is currently a premium member.

        :rtype: bool
        """

        return await self._state.is_premium(await self.id)

    async def _friends_iter(self):
        data = await self._state.get_user_friends(await self.id)
        return [User(state=self._state, data=friend) for friend in data]

    @property
    def friends(self):
        """
        :class:`.AsyncIterator` for this user's friends.

        Yields:
            :class:`User`
        """

        async def gen():
            for friend in await self._friends_iter():
                yield friend

        return AsyncIterator(gen=gen(), state=self._state)

    async def is_friends(self, other: User = None):
        """|coro|

        Checks whether this user is friends with another user or the client user.

        Args:
            other: User to check friendship with. If not specified, this will be the client user.
        """

        if self == other or not isinstance(other, BaseUser):
            return False

        if other:  # can't use API endpoint on user other than client
            await other._get_profile_data()
            return other in await self._friends_iter()

        other = other or self._state.client.user

        statuses = await self._state.check_status(await other.id, await self.id)

        return statuses[0]["status"] == "Friends"

    @property
    def followers(self):
        """
        :class:`.AsyncIterator` for user's followers.

        Yields:
            :class:`.User`
        """

        return FollowerList(state=self._state, opts={"user": self})

    @property
    def followings(self):
        """
        :class:`.AsyncIterator` for user's followings.

        Yields:
            :class:`.User`
        """

        return FollowingList(state=self._state, opts={"user": self})

    following = followings

    @cached_property
    def inventory(self):
        """
        :class:`.Inventory` for this user.
        """
        return Inventory(state=self._state, opts={"user": self})

    @property
    def games(self):
        """
        :class:`.AsyncIterator` for this user's games.

        Yields:
            :class:`.Universe`
        """

        access_filter = None

        async def gen():
            async for data in self._state.get_user_games(await self.id,
                                                         access_filter=str(access_filter) if access_filter else None):
                yield await self._state.client.get_universe(data["id"], data=data)

        return AsyncIterator(gen=gen())


class FollowerList(AsyncIterator):
    async def __aiter__(self):
        async for following_data in self._state.followers(await self._opts["user"].id):
            yield User(state=self._state, data=following_data)

    @async_property
    async def count(self):
        return await self._state.followings_count(await self._opts["user"].id)


class FollowingList(AsyncIterator):
    async def __aiter__(self):
        async for following_data in self._state.followings(await self._opts["user"].id):
            yield User(state=self._state, data=following_data)

    @async_property
    async def count(self):
        return await self._state.followings_count(await self._opts["user"].id)


class ClientUser(BaseUser, _ClientUser):
    """
    The ClientUser provides the same functionalities as :class:`User` as well as some
    methods that only apply to the client.

    **Operations**

        **x == y**

        Checks that two users are equal.

        **x != y**

        Checks that two users are not equal.
    """

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __repr__(self):
        return "ClientUser" + BaseUser.__repr__(self)[4:]

    def __hash__(self):
        return self._data["id"] or -2

    async def set_status(self, status: str):
        """|coro|

        Posts a new status to the client's profile.

        Args:
            status: New status to post.
        Returns:
            (str) Moderated status content.
        """

        data = await self._state.post_status(await self.id, status)

        self._update(data)
        return data["status"]

    @async_property
    async def robux(self):
        """|asyncprop|

        Amount of currency the client user has.

        :rtype: int
        """
        return (await self._state.get_currency(await self.id))["robux"]


class User(BaseUser, _User):
    """
    Represents a Roblox user.

    To get a specific user, use :meth:`.Roblox.get_user`

    **Operations**

        **x == y**

        Checks that two users are equal.

        **x != y**

        Checks that two users are not equal.

    """

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __hash__(self):
        return self._data["id"] or -2

    async def follow(self):
        """|coro|

        Follows the user from the client.
        """

        await self._state.follow(await self.id)
        log.debug("followed {}".format(self))

    async def unfollow(self):
        """|coro|

        Unfollows the user from the client.
        """

        await self._state.unfollow(await self.id)
        log.debug("unfollowed {}".format(self))

    async def request_friendship(self):
        """|coro|

        Sends a friend request to the user.
        """

        return await self._state.request_friendship(await self.id)

    async def unfriend(self):
        """|coro|

        Unfriends the user if friends.
        """

        await self._state.unfriend(await self.id)
        log.debug("unfriended {}".format(self))


class FriendRequest(User):
    """Represents a user requesting friendship with the client. This class is used to provide accept/decline methods
    while still allowing you to get user data."""

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
