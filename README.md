roblox.py
---------

**roblox.py** is a powerful object-oriented, asynchronous wrapper to the Roblox Web APIs.

See roblox.py in action:
```Python
from roblox import Roblox
import asyncio

async def main():
    client = Roblox()
    await client.login("username", "password")

    async for requester in client.get_friend_requests():
        mutual = False
        async for friend in client.user.friends:
            if await friend.is_friends(requester):
                mutual = True
                break

        if mutual:
            await requester.accept()
            print("Accepted {}".format(await requester.username))
        else:
            await requester.decline()
            print("Decline {}".format(await requester.username))

asyncio.get_event_loop().run_until_complete(main())
```