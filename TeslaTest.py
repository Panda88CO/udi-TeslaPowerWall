

from tesla_powerwall import Powerwall

PowerWall = Powerwall("192.168.1.151")
PowerWall.login("coe123COE", "christian.olgaard@gmail.com")
print(PowerWall.is_authenticated())
print(PowerWall.get_charge())
print(PowerWall.get_status())
print(PowerWall.get_grid_status())
meters = PowerWall.get_meters()



print(meters)
#PowerWall.logout()
