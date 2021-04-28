
import time
import json
from tesla_powerwall import Powerwall

def get(self, path: str, headers: dict = {}) -> dict:
    try:
        response = self._http_session.get(
            url=self.url(path),
            timeout=self._timeout,
            headers=headers,
        )
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout,
    ) as e:
        raise PowerwallUnreachableError(e)
    return(response)



PowerWall = Powerwall("192.168.1.151")
PowerWall.login("coe123COE", "christian.olgaard@gmail.com")
print(PowerWall.is_authenticated())
#print(PowerWall.get_charge())
#print(PowerWall.get_status())
#print(PowerWall.get_grid_status())
metersOld = PowerWall.get_meters()
#time.sleep(60)

for i in range(10):
    meters = PowerWall.get_meters()
    print(meters.solar.instant_power,meters.solar.energy_exported, meters.solar.energy_imported )
    print(meters.site.instant_power, meters.site.energy_exported, meters.site.energy_imported)
    print(meters.load.instant_power, meters.load.energy_exported, meters.load.energy_imported)
    print(meters.battery.instant_power, meters.battery.energy_exported, meters.battery.energy_imported)
    print()
    time.sleep(1)
print()


#print(PowerWall.run())
#print(PowerWall.stop())
#print(PowerWall.run())

print('get charge ') #needed
test1 = PowerWall.get_charge() #needed
print('\nget sitemaster ' )
test2 = PowerWall.get_sitemaster() #Needed

print('\n get Meters ' )
#print( PowerWall.get_meters())

print('\n get grid status ' ) # Needed
test3 = PowerWall.get_grid_status() # Needed

print('\n get grid services active ')
test4 = PowerWall.is_grid_services_active() # Needed
print('\nget grid services active ')
test5 = PowerWall.is_grid_services_active() # Needed
print('\n get grid services ')
test6 = PowerWall.get_site_info()

#print(PowerWall.set_site_name(, site_name: str))

print('\n get status ')
test7 = PowerWall.get_status() # NEeded
#print(PowerWall.get_grid_status()) # Needed


print('\nget device type ')
print( PowerWall.get_device_type())
print('\n get device serial number ')
print( PowerWall.get_serial_numbers())
print('\n get operation mode')
print(PowerWall.get_operation_mode()) #Needed

print('\n get backup percentage ')
print( PowerWall.get_backup_reserve_percentage()) #Needed
print('\n get solar system ')
print( PowerWall.get_solars())

print('\n get power weall Vin')
print( PowerWall.get_vin())

print('\n get power wall version ')
print( PowerWall.get_version())

print('\n get detect and pin version')
print( PowerWall.detect_and_pin_version())


#print(PowerWall.pin_version(, vers: Union[str, version.Version]))


print(PowerWall.get_pinned_version())


print(PowerWall.get_api())


print('close ')
PowerWall.close()
#print(PowerWall.logout())