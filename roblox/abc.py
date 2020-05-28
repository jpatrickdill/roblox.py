# ABC classes for Roblox

import abc
import asyncio


class User(metaclass=abc.ABCMeta):
    """An ABC that details common operations on a Roblox user.

    Attributes
    -----------
    username: :class:`str`
        The user's username.
    id: :class:`int`
        The user's Roblox ID.
    description: :class:`str`
        User description.
    status: :class:`str`
        User status.
    created_at: :class:`datetime.datetime`
        Time user was created.
    banned: :class:`bool`
        Whether user is banned.
    """

    @classmethod
    def __subclasshook__(cls, C):
        if cls is User:
            mro = C.__mro__
            for attr in ("username", "id", "description", "status", "created_at", "banned"):
                for base in mro:
                    if attr in base.__dict__:
                        break
                else:
                    return NotImplemented
            return True
        return NotImplemented

    @abc.abstractmethod
    async def friends(self):
        """
        Coroutine returns a list of the User's friends
        :return: list<:class:`User`>
        """
        pass

    @abc.abstractmethod
    async def followers(self):
        """
        Async Generator that yields user's followers
        :yields: :class:`User`
        """
        pass

    @abc.abstractmethod
    async def followings(self):
        """
        Async Generator that yields user's followings
        :yields: :class:`User`
        """
        pass


class Asset(metaclass=abc.ABCMeta):
    """An ABC that details common operations on a Roblox asset.

        Attributes
        -----------
        id: :class:`int`
            The asset's ID.
        product_id: :class:`int`
            The asset's product ID.
        name: :class:`str`
            The asset's name.
        description: :class:`str`
            The asset's description.
        created_at: :class:`datetime.datetime`
            The time the asset was created.
        updated_at: :class:`datetime.datetime`
            The time the asset was last updated.
        creator: :class:`User` or :class:`Group`
            Creator of the game.
        """
