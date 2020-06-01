import inspect

class AsyncIterator:
    """
    Async Iterator. You can iterate over this using the ``async for`` syntax::

        async for item in this_iterator:
            print(item)
    """

    __slots__ = ("_gen", "_state", "_opts")

    def __init__(self, *, gen=None, state=None, opts=None):
        self._gen = gen
        self._state = state
        self._opts = opts or {}

    def __aiter__(self):
        return self._gen

    async def flatten(self, limit=None):
        """
        Flattens iterator to a list of items.

        Args:
            limit: Max number of items to return in the list.

        :rtype: list
        """

        i = 0
        r = []
        async for obj in self:
            r.append(obj)

            i += 1
            if i == limit:
                break

        return r

    async def has(self, item):
        """
        Checks if an item exists in this iterator's values.

        :rtype: bool
        """

        async for obj in self:
            if item == obj:
                return True

        return False

    async def count(self):
        """
        Returns the number of items in this iterator.

        :rtype: int
        """

        return len(await self.flatten())

    async def find(self, predicate):
        """
        Attempts to find an object in the iterable given the predicate function.
        Predicate can be a normal function or coroutine.

        Args:
            predicate: Function or coroutine. Should return ``True`` if item matches or ``False`` if it doesn't.
        """

        async for obj in self:
            if inspect.iscoroutinefunction(predicate):
                matches = await predicate(obj)
            else:
                matches = predicate(obj)

            if matches:
                return obj

    async def find_all(self, predicate):
        """
        Finds all objects in the iterable that pass the predicate function.
        Predicate can be a normal function or coroutine.

        Args:
            predicate: Function or coroutine. Should return ``True`` if item matches or ``False`` if it doesn't.
        """

        r = []

        async for obj in self:
            if inspect.iscoroutinefunction(predicate):
                matches = await predicate(obj)
            elif callable(predicate):
                matches = predicate(obj)
            else:
                raise TypeError("Predicate must be either function or awaitable")

            if matches:
                r.append(obj)

        return r
