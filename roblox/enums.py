from enum import IntEnum, Enum


class AvatarType(Enum):
    R6 = "MorphToR6"
    R15 = "MorphToR15"


class AssetType(IntEnum):
    Image = 1
    TeeShirt = 2
    Audio = 3
    Mesh = 4
    Lua = 5
    Hat = 8
    Place = 9
    Model = 10
    Shirt = 11
    Pants = 12
    Decal = 13
    Head = 17
    Face = 18
    Gear = 19
    Badge = 21
    Animation = 24
    Torso = 27
    RightArm = 28
    LeftArm = 29
    LeftLeg = 30
    RightLeg = 31
    Package = 32
    GamePass = 34
    Plugin = 38
    MeshPart = 40
    HairAccessory = 41
    FaceAccessory = 42
    NeckAccessory = 43
    ShoulderAccessory = 44
    FrontAccessory = 45
    BackAccessory = 46
    WaistAccessory = 47
    ClimbAnimation = 48
    DeathAnimation = 49
    FallAnimation = 50
    IdleAnimation = 51
    JumpAnimation = 52
    RunAnimation = 53
    SwimAnimation = 54
    WalkAnimation = 55
    PoseAnimation = 56
    EarAccessory = 57
    Video = 62
