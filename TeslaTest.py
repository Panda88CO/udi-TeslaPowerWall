from api import API
from const import (
    DEFAULT_KW_ROUND_PERSICION,
    SUPPORTED_OPERATION_MODES,
    DeviceType,
    GridState,
    GridStatus,
    LineStatus,
    MeterType,
    OperationMode,
    Roles,
    SyncType,
    User,
)
from error import (
    AccessDeniedError,
    APIError,
    MissingAttributeError,
    PowerwallError,
    PowerwallUnreachableError,
)
from helpers import assert_attribute, convert_to_kw
from responses import (
    LoginResponse,
    Meter,
    MetersAggregates,
    PowerwallStatus,
    SiteInfo,
    SiteMaster,
    Solar,
)
from powerwall import Powerwall

PowerWall = Powerwall("192.168.1.151")
PowerWall.login("coe123COE", "christian.olgaard@gmail.com")
print(PowerWall.is_authenticated())
print(PowerWall.get_charge())
print(PowerWall.get_status())
meters = PowerWall.get_meters()


PowerWall.logout()


