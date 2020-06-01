from __future__ import annotations

import logging
from functools import wraps

import maya
from CaseInsensitiveDict import CaseInsensitiveDict
from async_property import async_property

from roblox.abc import Group as _Group
from roblox.abc import GroupMember as _GroupMember
from roblox.abc import Role as _Role
from roblox.abc import Shout as _Shout
from roblox.errors import *
from roblox.http import Session
from roblox.iterables import AsyncIterator
from roblox.user import User, BaseUser
from roblox.util import urlify
from typing import Union

log = logging.getLogger(__name__)


# util decorator
def g_info(name, nocache=False):
    """This decorator will check if the property is in the group"s _data, and if it isn"t send a request to the
    groups API endpoint"""

    def decorator(fn):
        @wraps(fn)
        async def new_fn(self):
            if nocache or self._data[name] is None:
                await self._get_group_details()

            return self._data[name]

        return new_fn

    return decorator


class Group(_Group):
    __slots__ = ("_data", "_state")

    def __init__(self, *, state: Session, data):
        self._state = state
        self._data = CaseInsensitiveDict({
            "id": None,
            "name": None,
            "description": None,
            "owner": None,
            "shout": None,
            "membercount": None,
            "isbuildersclubonly": None,
            "publicentryallowed": None,
            "islocked": None
        })
        self._update(data)

    def __repr__(self):
        return "Group({!r})".format(self._data["name"] or self._data["id"])

    def __hash__(self):
        return self._data["id"] or -2

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False

        return self._data["id"] == other._data["id"]

    def _update(self, data):
        self._data.update(data)

    async def _get_group_details(self):
        data = await self._state.get_group_details(await self.id)
        self._update(data)

    @async_property
    @g_info("id")
    async def id(self):
        """|asyncprop|

        The group's ID.

        :rtype: int
        """
        pass

    @async_property
    @g_info("name")
    async def name(self):
        """|asyncprop|

        The group's name.

        :rtype: str
        """
        pass

    @async_property
    @g_info("description")
    async def description(self):
        """|asyncprop|

        The group's description.

        :rtype: str
        """
        pass

    @async_property
    @g_info("publicentryallowed", nocache=True)
    async def is_public(self):
        """|asyncprop|

        Whether new members must be approved.

        :rtype: bool
        """
        pass

    @async_property
    async def owner(self):
        """|asyncprop|

        The group's owner.

        :rtype: :class:`.User`
        """

        await self._get_group_details()

        if self._data["owner"] is None:
            return None

        data = {
            "user": self._data["owner"],
            "role": (await self.roles)[-1]._data
        }

        return GroupMember(state=self._state, data=data, group=self)

    @async_property
    async def created_at(self):
        if self._data["shout"] is None:
            await self._get_group_details()

        raise NotImplemented

    updated_at = created_at

    @async_property
    async def url(self):
        """|asyncprop|

        The group's URL.

        :rtype: str
        """

        if self._data["id"] is None or self._data["name"] is None:
            await self._get_group_details()

        return "https://roblox.com/groups/{}/{}#!/about".format(self._data["id"], urlify(self._data["name"]))

    @async_property
    async def shout(self):
        """|asyncprop|

        The group's current shout.

        :rtype: :class:`.Shout`
        """

        await self._get_group_details()

        try:
            return Shout(state=self._state, data=self._data.get("shout"), group=self)
        except TypeError:
            return None

    @async_property
    async def roles(self, reverse=False):
        """|asyncprop|

        List of the group's roles.

        :rtype: List[:class:`.Role`]
        """

        data = await self._state.get_group_roles(await self.id)
        roles = []
        for role in data["roles"]:
            roles.append(
                Role(state=self._state, data=role, group=self)
            )

        roles.sort(key=lambda r: r._data["rank"], reverse=reverse)

        return roles

    async def get_role(self, role: Union[str, int]):
        """
        Attempts to find a role within a group given a name or ID.

        Args:
            role: Role's name or ID.

        :rtype: Optional[:class:`.Role`]
        """

        if isinstance(role, str) or isinstance(role, int):
            role = str(role).lower()

        for obj in await self.roles:
            if obj == role or str(await obj.id) == role or (await obj.name).lower() == role:
                return obj

    @property
    def members(self) -> _MembersIterator:
        """
        :class:`.AsyncIterator` for this group's members.

        Yields:
            :class:`.GroupMember`
        """

        return _MembersIterator(state=self._state, opts={"group": self})

    async def get_member(self, user):
        """
        Tries to find a group member given a username, ID, or :class:`.User`.

        Args:
            user: User to try and find within the group.

        :rtype: :class:`.GroupMember`
        """

        user_data = {}
        if isinstance(user, BaseUser):
            user_id = await user.id
            user_data = user._data
        elif isinstance(user, str):
            user = await self._state.client.get_user(username=user)
            user_id = await user.id
            user_data = user._data
        else:
            user_id = int(user)

        user_data["id"] = user_id

        all_roles = await self._state.get_user_roles(user_id)
        match = None
        for data in all_roles["data"]:
            if data["group"]["id"] == await self.id:
                match = data
                break
        if match is None:
            raise UserNotInGroup

        data = {
            "user": user_data,
            "role": match["role"]
        }

        return GroupMember(state=self._state, data=data, group=self)

    async def upload_asset(self, file, name, asset_type):
        if isinstance(file, str):
            file = open(file, "rb")

        r = await self._state.upload_asset(file, name, int(asset_type), group_id=await self.id)

        file.close()
        return r


class _MembersIterator(AsyncIterator):
    async def __aiter__(self):
        async for data in self._state.get_group_members(await self._opts["group"].id):
            yield GroupMember(state=self._state, data=data, group=self)

    async def count(self):
        await self._opts["group"]._get_group_details()
        return self._opts["group"]._data.get("membercount")


class Shout(_Shout):
    __slots__ = ("_data", "_state", "group")

    def __init__(self, *, state, data, group: Group):
        self._state = state
        self._data = CaseInsensitiveDict({
            "body": None,
            "poster": None,
            "created": None,
            "updated": None
        })
        self.group = group

        self._update(data)

    def __repr__(self):
        return "Shout({!r}, {!r}, {!r})".format(self.group,
                                                self._data["poster"]["username"],
                                                self._data["body"])

    def _update(self, data):
        self._data.update(data)

    @property
    def body(self):
        """
        Shout's body.

        :type: str
        """
        return self._data["body"]

    @property
    def created_at(self):
        """
        Date/time when the shout was last updated.

        :type: :class:`datetime.datetime`
        """
        try:
            return maya.parse(self._data["updated"]).datetime()
        except OSError:
            return None

    @async_property
    async def poster(self) -> Union[GroupMember, User]:
        """|asyncprop|

        User who posted the shout.

        Return:
            :class:`.GroupMember` if poster is still in the group, :class:`.User` otherwise.

        :rtype: Union[:class:`.GroupMember`, :class:`.User`]
        """

        poster_id = self._data["poster"]["userid"]
        poster_user = self._data["poster"]["username"]

        user = await self._state.client.get_user(id=poster_id, username=poster_user)
        try:  # try to get a GroupMember instead of User
            return await self.group.get_member(user)
        except UserNotInGroup:
            return user


class GroupMember(User, _GroupMember):
    """
    Represents a group member.

    This class inherits all functionality from :class:`.User`.

    **Operations**

        **x == y**

        Checks that two users are equal.

        **x != y**

        Checks that two users are not equal.

        **x > y**

        Checks that member X has a greater rank than member Y.

        **x >= y**

        Checks that member X's rank is greater than or equal to member Y.

        **x < y**

        Checks that member X has a lesser rank than member Y.

        **x <= y**

        Checks that member X's rank is less than or equal to member Y.

    Attributes:
        group (:class:`.Group`): Group the member belongs to.
    """
    __slots__ = ("_state", "_data", "group")

    def __init__(self, *, state, data, group):
        super().__init__(state=state, data=data.get("user", data.get("User")))
        self._data.update({
            "role": None
        })
        self._data.update(data)

        self.group = group

    def __repr__(self):
        return "GroupMember({!r}, group={!r}, rank={!r})".format(self._data["username"] or self._data["id"],
                                                                 self.group._data["name"] or self.group._data["id"],
                                                                 (self._data["role"] or {}).get("rank"))

    def _comp(self, other):
        if self._data["role"] is None:
            my_rank = 0
        else:
            my_rank = self._data["role"].get("rank", 0)

        if isinstance(other, GroupMember):
            if other._data["role"] is None:
                other_rank = 0
            else:
                other_rank = other._data["role"].get("rank", 0)
        elif isinstance(other, Role):
            other_rank = other._data.get("rank", 0)
        else:
            raise UserError("Can't compare GroupMember with {}".format(other.__class__.__name__))

        if my_rank > other_rank:
            return 1
        elif my_rank == other_rank:
            return 0
        else:
            return -1

    def __gt__(self, other):
        c = self._comp(other)

        return c == 1

    def __ge__(self, other):
        c = self._comp(other)

        return c > 0

    def __lt__(self, other):
        c = self._comp(other)

        return c == -1

    def __le__(self, other):
        c = self._comp(other)

        return c < 0

    @property
    def role(self):
        """
        Member's role within the group.

        :type: :class:`.Role`
        """
        if self._data["role"] is None:
            raise RoleNotFound

        return Role(state=self._state, data=self._data["role"], group=self.group)

    @async_property
    async def rank(self):
        """|asyncprop|

        Member's rank within the group. Shortcut for ``await member.role.rank`

        :rtype: int
        """

        return await self.role.rank


class Role(_Role):
    """
    Represents a roleset within a group.

    **Operations**

        **x == y**

        Checks that two roles are equal.

        **x != y**

        Checks that two roles are not equal.

        **x > y**

        Checks that role X has a greater rank than role Y.

        **x >= y**

        Checks that role X's rank is greater than or equal to role Y.

        **x < y**

        Checks that role X has a lesser rank than role Y.

        **x <= y**

        Checks that role X's rank is less than or equal to role Y.
    """

    __slots__ = ("_state", "_data", "group")

    def __init__(self, *, state: Session, data, group):
        self._state = state
        self._data = CaseInsensitiveDict({
            "id": None,
            "name": None,
            "description": None,
            "rank": None,
            "membercount": None,
            "permissions": None,
        })
        self._update(data)

        self.group = group

    def __repr__(self):
        return "Role({!r}, {!r}, rank={!r})".format(self.group, self._data["name"], self._data["rank"])

    def __hash__(self):
        return hash(self._data["id"] << 22 | self.group._data["id"])

    def __eq__(self, other):
        if not isinstance(other, Role):
            return False

        if self.group != other.group:
            return False

        return self._data["id"] == other._data["id"] and self._data["id"] is not None

    def _comp(self, other):
        if isinstance(other, Role):
            other = other._data["rank"]
        elif isinstance(other, GroupMember):
            if other._data["role"] is None:
                return False
            other = other._data["role"]["rank"]

        if self._data["rank"] > other:
            return 1
        elif self._data["rank"] < other:
            return -1
        else:
            return 0

    def __gt__(self, other):
        c = self._comp(other)

        return c == 1

    def __ge__(self, other):
        c = self._comp(other)

        return c >= 0

    def __lt__(self, other):
        c = self._comp(other)

        return c == -1

    def __le__(self, other):
        c = self._comp(other)

        return c <= 0

    def _update(self, data):
        self._data.update(data)

    async def _get_role_details(self):
        data = await self._state.get_role_details(await self.id)
        data = data["data"][0]
        self._update(data)

    @async_property
    async def id(self):
        """|asyncprop|

        The role's ID.

        :rtype: int
        """
        return self._data["id"]

    @async_property
    async def name(self):
        """|asyncprop|

        The role's name.

        :rtype: str
        """
        if self._data["name"] is None:
            await self._get_role_details()
        return self._data["name"]

    @async_property
    async def description(self):
        """|asyncprop|

        The role's description.

        :rtype: str
        """
        if self._data["description"] is None:
            await self._get_role_details()
        return self._data["description"]

    @async_property
    async def rank(self):
        """|asyncprop|

        The role's integer rank.

        :rtype: int
        """
        if self._data["rank"] is None:
            await self._get_role_details()
        return self._data["rank"]

    @async_property
    async def member_count(self):
        """|asyncprop|

        Number of members belonging to this role.

        :rtype: int
        """
        await self._get_role_details()

        return self._data["membercount"]
