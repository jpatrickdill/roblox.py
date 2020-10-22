class RobloxException(Exception):
    pass


class RateLimit(RobloxException):
    pass


# AUTH ERRORS

class AuthError(RobloxException):
    pass


class Captcha(AuthError):
    pass


# USER ERRORS

class UserError(RobloxException):
    pass


class FriendLimitExceeded(UserError):
    pass


class UserIdentificationError(UserError):
    pass


# ASSET ERRORS

class AssetError(RobloxException):
    pass


class AssetNotFound(AssetError):
    pass


# PURCHASE ERRORs

class PurchaseError(AssetError):
    pass


class PriceChanged(PurchaseError):
    pass


# GAME ERRORS

class GameNotFound(AssetNotFound):
    pass


# GROUP ERRORS

class GroupError(RobloxException):
    pass


class GroupNotFound(GroupError):
    pass


class UserNotInGroup(GroupError):
    pass


class RoleError(GroupError):
    pass


class RoleNotFound(RoleError):
    pass


class RoleEditError(RoleError):
    pass
