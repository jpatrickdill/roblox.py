# This module handles all API calls
import asyncio
import logging
import re

import aiohttp
from aiohttp import FormData
import chardet

from roblox.errors import *

log = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Saf" \
             "ari/537.36"

# util
xsrf = re.compile(r"setToken\('(.{4,16})'\);")
url = re.compile("<url>(.+)</url>")
rvt = re.compile(r'<input name="?__RequestVerificationToken"?[ \w=]+value="?(\S+)"?>')


# base URLs
class Url:
    Roblox = "https://www.roblox.com"
    Api = "https://api.roblox.com"
    Auth = "https://auth.roblox.com/v2"
    Users = "https://users.roblox.com/v1"
    Friends = "https://friends.roblox.com/v1"
    Premium = "https://premiumfeatures.roblox.com/v1"
    Inventory = "https://inventory.roblox.com/v2"
    Catalog = "https://catalog.roblox.com/v1"
    Game1 = "https://games.roblox.com/v1"
    Game2 = "https://games.roblox.com/v2"
    Economy = "https://economy.roblox.com/v1"
    Economy2 = "https://economy.roblox.com/v2"
    AssetDelivery = "https://assetdelivery.roblox.com/v1"
    Group1 = "https://groups.roblox.com/v1"
    Group2 = "https://groups.roblox.com/v2"
    Develop = "https://develop.roblox.com/v1"
    ItemConfig = "https://itemconfiguration.roblox.com/v1"


def ok(resp):
    # True if response is OK
    return 200 <= (resp if isinstance(resp, int) else resp.status) < 300


class Session:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

        self.client = None

        self.token = None

        self.session = aiohttp.ClientSession(headers={
            "User-Agent": USER_AGENT
        })

    async def close(self):
        await self.session.close()

    def update_token(self, text):
        # attempts to extract and update token from response

        match = xsrf.search(text)
        if match:
            self.token = match.group(1)
            log.info("Updated XSRF token: {!r}".format(self.token))

    def get_rvt(self, text):
        # attempts to get RequestVerificationToken from HTML

        match = rvt.search(text)
        if match:
            return match.group(1)

    def req(self, *args, **kwargs):
        # prepared request method
        # use this for ALL API CALLS for CONSISTENCY

        headers = kwargs.get("headers", {})

        if self.token is not None:
            headers.setdefault("X-CSRF-TOKEN", self.token)

        kwargs["headers"] = headers

        return self.session.request(*args, **kwargs)

    async def login(self, username=None, password=None):
        """
        Attempt to login user, return True if successful
        """
        payload = {
            "ctype": "Username",
            "cvalue": username or self.username,
            "password": password or self.password
        }

        # first get token
        async with self.req("get", Url.Roblox + "/login") as resp:
            self.update_token(await resp.text())

        async with self.req("post", Url.Auth + "/login", json=payload) as resp:
            if not ok(resp):
                data = await resp.json()
                print(data)

                if "errors" not in data or len(data["errors"]) == 0:
                    raise AuthError("Login failed", resp.status)

                err = data["errors"][0]
                if err["code"] == 2:
                    raise Captcha("Login failed: {}".format(err["message"]))
                else:
                    raise AuthError("Login failed: {}".format(err["message"]))
            else:
                # update data in case login different

                self.username = username or self.username
                self.password = password or self.password

                log.info("Logged in as {!r}".format(self.username))

    async def manual_auth(self, username, cookie):
        cookies = {".ROBLOSECURITY": cookie}

        await self.session.close()
        self.session = aiohttp.ClientSession(headers={
            "User-Agent": USER_AGENT
        }, cookies=cookies)

        self.username = username

        async with self.req("get", Url.Roblox + "/home") as resp:
            if ok(resp):
                log.info("Opened new session with ROBLOSECURITY cookie")

                self.update_token(await resp.text())
            else:
                raise AuthError("Invalid security cookie")

    async def logout(self):
        """*
        De-authorizes user.
        """
        async with self.req("post", Url.Auth + "/logout") as resp:
            return ok(resp)

    async def is_authorized(self):
        """
        Checks if user is authorized. Returns bool
        :return:
        """

        async with self.req("get", Url.Roblox + "/home") as resp:
            return ok(resp)

    async def refresh_csrf(self):
        pass

    async def my_settings(self):
        async with self.req("get", Url.Roblox + "/my/settings/json") as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise AuthError

    async def gen_pages(self, url, params=None, data_key="data", sleep=0):
        # turns paged API into a generator

        params = params or {}
        params.setdefault("limit", 100)

        i = 1
        while True:
            log.debug("page {}".format(i))

            async with self.req("get", url, params=params) as resp:
                data = await resp.json()
                for item in data.get(data_key, []):
                    yield item

                cursor = data.get("nextPageCursor")
                params.update(cursor=cursor)

                if cursor is None:
                    break

            if sleep > 0:
                await asyncio.sleep(sleep)

            i += 1

    async def get_by_username(self, username):
        """
        Gets user Id and Username
        """

        async with self.req("get", Url.Api + "/users/get-by-username", params={"username": username}) as resp:
            if not ok(resp):
                raise UserIdentificationError("User {!r} not found".format(username))

            return {"id": (await resp.json())["Id"]}

    async def get_user_data(self, user_id):
        async with self.req("get", Url.Users + "/users/{}".format(user_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise UserIdentificationError("User {!r} not found".format(user_id))

    async def is_premium(self, user_id):
        async with self.req("get", Url.Premium + "/users/{}/validate-membership".format(user_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise AuthError

    async def user_status(self, user_id):
        async with self.req("get", Url.Users + "/users/{}/status".format(user_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise UserIdentificationError("User {!r} not found".format(user_id))

    async def post_status(self, user_id, status):
        payload = {
            "status": status
        }

        async with self.req("patch", Url.Users + "/users/{}/status".format(user_id), json=payload) as resp:
            if ok(resp):
                return await resp.json()
            else:
                if resp.status == 403:
                    raise AuthError("Not authorized to update status")
                else:
                    raise UserError

    async def get_user_friends(self, user_id):
        async with self.req("get", Url.Friends + "/users/{}/friends".format(user_id)) as resp:
            if resp.status == 404:
                raise UserIdentificationError("User {!r} not found".format(user_id))

            return (await resp.json())["data"]

    async def check_status(self, user_id, compare):
        if isinstance(compare, int):
            compare = [compare]

        url = Url.Friends + "/users/{}/friends/statuses".format(user_id)
        params = {"userIds": ",".join([str(c) for c in compare])}

        async with self.req("get", url, params=params) as resp:
            data = await resp.json()

            if not ok(resp):
                err = data["errors"][0]["code"]
                if err == 1:
                    raise UserIdentificationError("Target user is invalid or does not exist")
                else:
                    raise UserError

            if ok(resp):
                return data["data"]

    async def unfriend(self, user_id):
        async with self.req("post", Url.Friends + "/users/{}/unfriend".format(user_id)) as resp:
            if ok(resp):
                return True
            else:
                if resp.status == 400:
                    raise UserIdentificationError
                else:
                    raise UserError

    async def get_friend_requests(self):
        async for data in self.gen_pages(Url.Friends + "/my/friends/requests"):
            yield data

    async def friend_request_count(self):
        async with self.req("get", Url.Friends + "/user/friend-requests/count") as resp:
            if ok(resp):
                return (await resp.json())["count"]
            else:
                raise AuthError

    async def decline_all_friend_requests(self):
        async with self.req("post", Url.Friends + "/user/friend-requests/decline-all",
                            headers={"Host": "friends.roblox.com"}) as resp:
            if ok(resp):
                return True
            else:
                raise AuthError(await resp.text())

    async def accept_friend_request(self, user_id):
        async with self.req("post", Url.Friends + "/users/{}/accept-friend-request".format(user_id)) as resp:
            if not ok(resp):
                data = await resp.json()
                err = data["errors"][0]

                if err["code"] == 1:
                    raise UserIdentificationError("User {!r} not found".format(user_id))
                elif err["code"] == 10:
                    raise UserError("Friend request does not exist")
                elif err["code"] in (11, 12):
                    raise FriendLimitExceeded("Friend limit exceeded")
            else:
                return True

    async def decline_friend_request(self, user_id):
        async with self.req("post", Url.Friends + "/users/{}/decline-friend-request".format(user_id)) as resp:
            if not ok(resp):
                data = await resp.json()
                err = data["errors"][0]

                if err["code"] == 1:
                    raise UserIdentificationError("User {!r} not found".format(user_id))
                elif err["code"] == 10:
                    raise UserError("Friend request does not exist")
            else:
                return True

    async def request_friendship(self, user_id):
        async with self.req("post", Url.Friends + "/users/{}/request-friendship".format(user_id)) as resp:
            data = await resp.json()

            if data.get("success", False):
                return True
            elif data.get("isCaptchaRequired", False):
                raise Captcha("Captcha required")
            else:
                code = data["errors"][0]["code"]
                if code == 1:
                    raise UserIdentificationError
                elif code == 5:
                    raise UserError("Already friends with {!r}".format(user_id))
                elif code == 7:
                    raise UserError("Can't send friend request to self")
                elif code == 10:
                    raise UserIdentificationError("User {!r} doesn't exist".format(user_id))
                else:
                    raise UserError("{}".format(code))

    # async def unfriend(self, user_id):
    #     async with self.req("post", Url.Friends + "/users/{}/unfriend".format(user_id)) as resp:
    #         data = await resp.json()
    #
    #         if data.get("success", False):
    #             return True
    #         elif data.get("isCaptchaRequired", False):
    #             raise Captcha("Captcha required")
    #         else:
    #             code = data["errors"][0]["code"]
    #             if code == 1:
    #                 raise UserIdentificationError
    #             elif code == 5:
    #                 raise UserError("Not friends with {!r}".format(user_id))
    #             elif code == 7:
    #                 raise UserError("Can't unfriend self")
    #             elif code == 10:
    #                 raise UserIdentificationError("User {!r} doesn't exist".format(user_id))
    #             else:
    #                 raise UserError("{}".format(code))

    async def follow(self, user_id):
        async with self.req("post", Url.Friends + "/users/{}/follow".format(user_id)) as resp:
            if ok(resp):
                return True
            else:
                print(await resp.json())
                if resp.status == 400:
                    raise UserIdentificationError
                else:
                    raise UserError

    async def unfollow(self, user_id):
        async with self.req("post", Url.Friends + "/users/{}/unfollow".format(user_id)) as resp:
            if ok(resp):
                return True
            else:
                if resp.status == 400:
                    raise UserIdentificationError
                else:
                    raise UserError

    async def follower_count(self, user_id):
        async with self.req("get", Url.Friends + "/users/{}/followers/count".format(user_id)) as resp:
            if ok(resp):
                return (await resp.json())["count"]
            else:
                if resp.status == 400:
                    raise UserIdentificationError
                else:
                    raise UserError

    async def followers(self, user_id):
        async for data in self.gen_pages(Url.Friends + "/users/{}/followers".format(user_id)):
            yield data

    async def followings_count(self, user_id):
        async with self.req("get", Url.Friends + "/users/{}/followings/count".format(user_id)) as resp:
            if ok(resp):
                return (await resp.json())["count"]
            else:
                if resp.status == 400:
                    raise UserIdentificationError
                else:
                    raise UserError

    async def followings(self, user_id):
        async for data in self.gen_pages(Url.Friends + "/users/{}/followings".format(user_id)):
            yield data

    async def inventory_by_type(self, user_id, asset_type):
        async for data in self.gen_pages(Url.Inventory + "/users/{}/inventory/{}".format(user_id, asset_type)):
            yield data

    async def product_info(self, asset_id):
        async with self.req("get", Url.Api + "/marketplace/productinfo", params={"assetId": asset_id}) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise AssetNotFound

    async def get_currency(self, user_id):
        async with self.req("get", Url.Economy + "/users/{}/currency".format(user_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise AuthError

    async def purchase_product(self, product_id, expected_price, expected_seller):
        payload = {
            "expectedCurrency": 1,
            "expectedPrice": expected_price,
            "expectedSellerId": expected_seller
        }

        async with self.req("post", Url.Economy + "/purchases/products/{}".format(product_id), json=payload) as resp:
            data = await resp.json()
            if data["purchased"]:
                return data
            else:
                reason = data.get("reason")
                if reason == "InvalidArguments":
                    raise PurchaseError(data.get("errorMsg"))
                elif reason == "PriceChanged":
                    raise PriceChanged(data.get("errorMsg"))
                else:
                    raise PurchaseError(data.get("errorMsg"))

    async def has_asset(self, user_id, asset_id):
        async with self.req("get", Url.Api + "/ownership/hasasset", params={"userId": user_id,
                                                                            "assetId": asset_id}) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise UserError(await resp.text())

    async def favorites_count(self, asset_id):
        async with self.req("get", Url.Catalog + "/favorites/assets/{}/count".format(asset_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise AssetNotFound

    async def favorite_model(self, user_id, asset_id):
        async with self.req("get",
                            Url.Catalog + "/favorites/users/{}/assets/{}/favorite".format(user_id, asset_id)) as resp:
            return await resp.json()

    async def delete_favorite(self, user_id, asset_id):
        async with self.req("delete",
                            Url.Catalog + "/favorites/users/{}/assets/{}/favorite".format(user_id, asset_id)) as resp:
            if ok(resp):
                return True
            else:
                data = await resp.json()
                code = data["errors"][0]["code"]

                if resp.status == 400:
                    raise AssetNotFound
                elif resp.status == 403:
                    if code in (0, 6):
                        raise AuthError
                    elif code == 7:
                        raise Captcha
                elif resp.status == 409:
                    raise AssetError("Asset already not favorited")

    async def create_favorite(self, user_id, asset_id):
        async with self.req("post",
                            Url.Catalog + "/favorites/users/{}/assets/{}/favorite".format(user_id, asset_id)) as resp:
            if ok(resp):
                return True
            else:
                data = await resp.json()
                code = data["errors"][0]["code"]

                if resp.status == 400:
                    raise AssetNotFound
                elif resp.status == 403:
                    if code in (0, 6):
                        raise AuthError
                    elif code == 7:
                        raise Captcha
                elif resp.status == 409:
                    raise AssetError("Asset already favorited")

    async def universe_favorited(self, universe_id):
        async with self.req("get", Url.Game1 + "/games/{}/favorites".format(universe_id)) as resp:
            if ok(resp):
                return await resp.json()
            elif resp.status == 400:
                raise GameNotFound("Invalid Root Place")
            elif resp.status == 401:
                raise AuthError
            elif resp.status == 400:
                raise GameNotFound

    async def universe_favorites(self, universe_id):
        async with self.req("get", Url.Game1 + "/games/{}/favorites/count".format(universe_id)) as resp:
            if ok(resp):
                return await resp.json()
            elif resp.status == 400:
                raise GameNotFound("Invalid Root Place")
            elif resp.status == 401:
                raise AuthError
            elif resp.status == 400:
                raise GameNotFound

    async def favorite_universe(self, universe_id, favorite):
        payload = {
            "isFavorited": favorite
        }
        async with self.req("post", Url.Game1 + "/games/{}/favorites".format(universe_id), json=payload) as resp:
            data = await resp.json()
            if ok(resp):
                return data
            elif resp.status == 400:
                raise GameNotFound("Invalid Root Place")
            elif resp.status == 401:
                raise AuthError
            elif resp.status == 400:
                raise GameNotFound
            else:
                raise UserError(str(data))

    async def get_place_details(self, *place_id):
        ids = ",".join([str(i) for i in place_id])
        async with self.req("get", Url.Game1 + "/games/multiget-place-details", params={"placeIds": ids}) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise GameNotFound

    async def get_game_details(self, *universe_id):
        ids = ",".join([str(i) for i in universe_id])
        async with self.req("get", Url.Game1 + "/games", params={"universeIds": ids}) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise GameNotFound

    async def get_user_games(self, user_id, access_filter=None):
        p = {}
        if access_filter is not None:
            p["accessFilter"] = access_filter

        async for data in self.gen_pages(Url.Game2 + "/users/{}/games".format(user_id),
                                         params=p):
            yield data

    async def download_asset(self, asset_id, fp):
        async with self.req("get", Url.AssetDelivery + "/asset/", params={"id": asset_id}) as resp:
            if ok(resp):
                content = await resp.read()
                encoding = chardet.detect(content)["encoding"]
                if encoding:
                    text = content.decode(encoding)
                    if text.startswith("<roblox"):
                        log.debug("xml content redirect")
                        real_url = url.search(text)
                        if real_url:
                            async with self.req("get", real_url.group(1)) as content:
                                if not ok(resp):
                                    if resp.status == 403:
                                        raise AuthError("No permission to download asset")
                                fp.write(await content.read())
                        else:
                            raise AssetError("Content not found")
                else:
                    fp.write(await resp.read())
            else:
                if resp.status == 409:
                    raise AuthError("Not authorized to download asset")

    async def delete_from_inventory(self, asset_id):
        async with self.req("post", Url.Roblox + "/asset/delete-from-inventory", params={"assetId": asset_id}) as resp:
            if ok(resp):
                return True
            else:
                raise AssetError

    async def configure_asset_sales(self, asset_id, payload, release):
        path = "release" if release else "update-price"

        async with self.req("get", Url.Roblox + "/catalog/configure?id={}#!/sales".format(asset_id)) as resp:
            self.update_token(await resp.text())

        async with self.req("post", Url.ItemConfig + "/assets/{}/{}".format(asset_id, path), json=payload) as resp:
            if ok(resp):
                return True
            else:
                raise AssetError(await resp.json())

    async def configure_asset(self, asset_id, payload):
        async with self.req("patch", Url.Develop + "/assets/{}/".format(asset_id), json=payload) as resp:
            if ok(resp):
                return True
            else:
                raise AssetError(await resp.text())

    async def upload_asset(self, file, name, asset_type, group_id=None):
        rvturl = Url.Roblox + "/develop"
        if group_id is not None:
            rvturl = Url.Roblox + "/develop/groups/{}".format(group_id)

        async with self.req("get", rvturl, params={"View": asset_type}) as resp:
            rvt = self.get_rvt(await resp.text())
            if rvt is None:
                print(resp.status, resp.url)
                raise AuthError("No Request Verification Token Found")
            log.debug("__RequestVerificationToken: {}".format(rvt))

        form = aiohttp.FormData({
            "__RequestVerificationToken": str(rvt),
            "assetTypeId": str(asset_type),
            "name": name,
            "isOggUploadEnabled": "True",
            "isTgaUploadEnabled": "True",
            # "onVerificationPage": "False",
            "captchaEnabled": "False"
        })

        form.add_field("file", file)

        if group_id is not None:
            form.add_field("groupId", str(group_id))

        async with self.req("post", Url.Roblox + "/build/upload", data=form) as resp:
            print(resp.status)
            print(resp.url)

            print(resp.headers.get("location"))

            return resp.url, resp.headers.get("location")

    async def get_group_details(self, group_id):
        async with self.req("get", Url.Group1 + "/groups/{}".format(group_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise GroupNotFound("Couldn't find group {!r}".format(group_id))

    async def get_group_roles(self, group_id):
        async with self.req("get", Url.Group1 + "/groups/{}/roles".format(group_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise GroupNotFound("Couldn't find group {!r}".format(group_id))

    async def get_group_members(self, group_id):
        async for data in self.gen_pages(Url.Group1 + "/groups/{}/users".format(group_id)):
            yield data

    async def get_role_members(self, group_id, role_id):
        async for data in self.gen_pages(Url.Group1 + "/groups/{}/roles/{}/users".format(group_id, role_id)):
            yield data

    async def get_role_details(self, *role_id):
        role_ids = ",".join([str(i) for i in role_id])
        async with self.req("get", Url.Group1 + "/roles", params={"ids": role_ids}) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise RoleNotFound

    async def get_user_roles(self, user_id):
        async with self.req("get", Url.Group1 + "/users/{}/groups/roles".format(user_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                print(await resp.text())
                raise UserError

    async def set_member_role(self, group_id, user_id, role_id):
        payload = {
            "roleId": role_id
        }

        async with self.req("patch",
                            Url.Group1 + "/groups/{}/users/{}".format(group_id, user_id), json=payload) as resp:
            if ok(resp):
                return True
            else:
                raise RoleError(await resp.text())

    async def configure_role(self, group_id, role_id, vals):
        async with self.req("patch",
                            Url.Group1 + "/groups/{}/rolesets/{}".format(group_id, role_id), json=vals) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise RoleEditError(await resp.text())

    async def get_permissions(self, group_id):
        async with self.req("get", Url.Group1 + "/groups/{}/roles/permissions".format(group_id)) as resp:
            if ok(resp):
                return await resp.json()
            else:
                raise RoleError(await resp.text())

    async def edit_permissions(self, group_id, role_id, new_perms):
        payload = {
            "permissions": new_perms
        }
        async with self.req("patch", Url.Group1 + "/groups/{}/roles/{}/permissions".format(group_id, role_id),
                            json=payload) as resp:
            if ok(resp):
                return True
            else:
                raise PermissionError(await resp.text())

    # game servers

    async def get_game_servers(self, place_id, server_type):
        async for data in self.gen_pages(Url.Game1 + "/games/{}/servers/{}".format(place_id, server_type)):
            yield data


