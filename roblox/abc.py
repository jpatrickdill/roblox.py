# ABC classes for Roblox

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Union

from roblox.enums import AssetType


class User(metaclass=ABCMeta):
    """An ABC that details common operations on a Roblox user."""

    # @classmethod
    # def __subclasshook__(cls, C):
    #     if cls is User:
    #         mro = C.__mro__
    #         for attr in ("username", "id", "description", "status", "created_at", "banned"):
    #             for base in mro:
    #                 if attr in base.__dict__:
    #                     break
    #             else:
    #                 return NotImplemented
    #         return True
    #     return NotImplemented

    @property
    @abstractmethod
    async def id(self) -> int:
        """
        Async property that returns the User's ID.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def username(self) -> str:
        """
        Async property that returns the User's username.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def url(self) -> str:
        """
        Async property that returns the User's profile URL.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def created_at(self) -> datetime:
        """
        Async property that returns the datetime at which the user was created.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def description(self) -> str:
        """
        Async property that returns the User's profile description.
        """
        raise NotImplemented

    @abstractmethod
    async def status(self) -> str:
        """
        Returns the User's current status.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def is_banned(self) -> bool:
        """
        Async property that returns whether the user is banned.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def is_premium(self) -> bool:
        """
        Async property that returns whether the user has a premium subscription.
        """
        raise NotImplemented

    @abstractmethod
    async def friends(self) -> AsyncGenerator[User]:
        """
        Async Generator yielding the user's friends.
        """
        raise NotImplemented

    @abstractmethod
    async def is_friends(self, other: Optional[User] = None) -> bool:
        """
        Checks whether this user is friends with another user or the client user.
        """
        raise NotImplemented

    @property
    @abstractmethod
    def followers(self):
        """
        Property that returns FollowerList for this user.
        """
        raise NotImplemented

    @property
    @abstractmethod
    def followings(self):
        """
        Property that returns FollowingsList for this user.
        """
        raise NotImplemented

    @property
    @abstractmethod
    def inventory(self):
        """
        Property that returns Inventory for this user.
        """
        raise NotImplemented

    @abstractmethod
    def games(self) -> AsyncGenerator[Universe, None]:
        """
        Async Generator that yields the user's games.
        """
        raise NotImplemented


class ClientUser(metaclass=ABCMeta):
    """An ABC that details operations on the client user."""

    @abstractmethod
    async def set_status(self, status: str) -> str:
        """
        Sets the client user's status.
        :param status: New status.
        :return: Moderated status.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def robux(self) -> int:
        """
        Returns the client user's amount of currency.
        """


class OtherUser(metaclass=ABCMeta):
    """An ABC that details operations on non-client users."""

    async def follow(self):
        """Follows this user from the client user."""
        raise NotImplemented

    async def unfollow(self):
        """Unfollows this user from the client user."""
        raise NotImplemented

    async def request_friendship(self):
        """Sends a friend request to this user."""
        raise NotImplemented

    async def unfriend(self):
        """Unfriends this user.."""
        raise NotImplemented


class DisplayPage(metaclass=ABCMeta):
    """An ABC that details an object with a display page, such as an asset, place, or universe."""

    @property
    @abstractmethod
    async def id(self) -> int:
        """
        Async property that returns the object's ID.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def name(self) -> str:
        """
        Async property that returns the object's name.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def description(self) -> str:
        """
        Async property that returns the object's description.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def url(self) -> str:
        """
        Async property that returns the object's URL.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def created_at(self) -> datetime:
        """
        Async property that returns when the object was created.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def updated_at(self) -> datetime:
        """
        Async property that returns when the object was last updated.
        """
        raise NotImplemented


class Votable(metaclass=ABCMeta):
    """ABC that represents on object that can be voted on, e.g., favorites, thumbs-up, thumbs-down"""

    @property
    @abstractmethod
    async def favorites(self) -> int:
        """
        Async property that returns the asset's current number of favorites.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def is_favorited(self) -> bool:
        """
        Async property that returns whether the asset is favorited by the client.
        """
        raise NotImplemented

    @abstractmethod
    async def favorite(self):
        """
        Favorites the asset for the client user.
        """
        raise NotImplemented

    @abstractmethod
    async def unfavorite(self):
        """
        Unfavorites the asset for the client user.
        """
        raise NotImplemented


class Asset(DisplayPage, Votable, metaclass=ABCMeta):
    """An ABC that details common operations on a Roblox asset."""

    @property
    @abstractmethod
    async def type(self) -> AssetType:
        """
        Async property that returns the Asset's type.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def price(self) -> int:
        """
        Async property that returns the asset's current price in Robux.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def for_sale(self) -> bool:
        """
        Async property that returns whether the asset can be purchased.
        """
        raise NotImplemented

    @property
    @abstractmethod
    async def creator(self) -> User:
        """
        Async property that returns the creator of the asset.
        """
        raise NotImplemented

    @abstractmethod
    async def purchase(self, expected_price: Optional[int] = None):
        """
        Purchases the asset for the client user. If `expected_price` is specified, the asset will not be
        purchased unless the `expected_price` matches the current price.
        """
        raise NotImplemented

    @abstractmethod
    async def delete(self):
        """
        Deletes asset from the client user's inventory.
        """


class Place(Asset, metaclass=ABCMeta):
    """An ABC that details operations on a Roblox Place asset."""

    @property
    @abstractmethod
    async def universe(self) -> Universe:
        """Async property that returns the Universe the place belongs to."""
        raise NotImplemented


class Universe(DisplayPage, Votable, metaclass=ABCMeta):
    """An ABC that details common operations on a Roblox Universe (Game)."""

    @property
    @abstractmethod
    async def visits(self) -> int:
        """Async property that returns the number of visits to this game."""
        raise NotImplemented

    @property
    @abstractmethod
    async def playing(self) -> int:
        """Async property that returns the number of players in this game."""
        raise NotImplemented

    @property
    @abstractmethod
    async def max_players(self) -> int:
        """Async property that returns the max players per server in this game."""
        raise NotImplemented

    @property
    @abstractmethod
    async def root_place(self) -> Place:
        """Async property that returns the universe's root place."""
        raise NotImplemented


class Server(metaclass=ABCMeta):
    """An ABC that details common operations on a Roblox game server."""

    @property
    @abstractmethod
    async def id(self) -> str:
        """Async property that returns the server's UUID."""
        raise NotImplemented

    @property
    @abstractmethod
    async def playing(self) -> int:
        """Async property that returns the number of players in this server."""
        raise NotImplemented

    @property
    @abstractmethod
    async def max_players(self) -> int:
        """Async property that returns the max number of players in the server."""
        raise NotImplemented

    @property
    @abstractmethod
    async def access_code(self) -> str:
        """Access code used to join the game."""
        raise NotImplemented


class Group(DisplayPage, metaclass=ABCMeta):
    """ABC detailing operations on a Roblox Group."""

    @property
    @abstractmethod
    async def owner(self) -> Optional[User]:
        """Async property that returns the group's current owner, if it has one."""
        raise NotImplemented

    @property
    @abstractmethod
    async def shout(self) -> Optional[Shout]:
        """Async property that returns the group's current shout."""
        raise NotImplemented

    @property
    @abstractmethod
    async def members(self) -> AsyncGenerator[GroupMember, None]:
        """Async generator that yields the group's members."""
        raise NotImplemented

    @abstractmethod
    async def get_member(self, user: Union[User, str, int]) -> GroupMember:
        """Tries to find a group member given a username, user ID, or User object."""
        raise NotImplemented

    @property
    @abstractmethod
    async def is_public(self) -> bool:
        """Async property that returns whether the group allows public entry."""
        raise NotImplemented

    @property
    @abstractmethod
    async def roles(self) -> List[Role]:
        """Async property that returns a list of the group's roles"""
        raise NotImplemented


class GroupMember(User, metaclass=ABCMeta):
    """ABC describing operations on a Group Member."""

    @property
    @abstractmethod
    async def role(self) -> Role:
        """Async property that eturns the member's group role."""
        raise NotImplemented

    @abstractmethod
    async def change_role(self, role):
        """Changes member's role in group."""
        raise NotImplemented

    @property
    @abstractmethod
    async def rank(self) -> int:
        """Shortcut for the numerical rank of the member's role."""
        raise NotImplemented


class Role(metaclass=ABCMeta):
    """ABC describing a group roleset."""

    @property
    @abstractmethod
    async def id(self) -> int:
        """Async property that returns the role's ID."""
        raise NotImplemented

    @property
    @abstractmethod
    async def name(self) -> str:
        """Async property that returns the role's name."""
        raise NotImplemented

    @property
    @abstractmethod
    async def description(self) -> str:
        """Async property that returns the role's description."""
        raise NotImplemented

    @property
    @abstractmethod
    async def rank(self) -> int:
        """Async property that returns the role's numerical rank."""
        raise NotImplemented

    @property
    @abstractmethod
    def members(self):
        """Members of this role."""
        raise NotImplemented


class Shout(metaclass=ABCMeta):
    """ABC describing a group shout."""

    @property
    @abstractmethod
    def body(self) -> str:
        """Returns the shout's body."""
        raise NotImplemented

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Returns the time the shout was created at."""
        raise NotImplemented

    @property
    @abstractmethod
    async def poster(self) -> User:
        """Returns the user who posted the shout."""
        raise NotImplemented
