

from api import API
'''
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

'''
import requests
import json

powerwallStr = "https://192.168.1.151/api/"
login = "login/Basic"

password='coe123COE',
email='christian.olgaard@gmail.com',
usertype = 'customer'

testPW = API( "192.168.1.151", 10, None, False, True)
response = testPW.login(usertype, email, password, False)
print(testPW.is_authenticated())


#resp = requests.put(loginstr, json=credentials, verify=False)
'''
PowerWall = Powerwall("192.168.1.151")
PowerWall.login("coe123COE", "christian.olgaard@gmail.com")
print(PowerWall.is_authenticated())
print(PowerWall.get_charge())
print(PowerWall.get_status())
meters = PowerWall.get_meters()


PowerWall.logout()
'''