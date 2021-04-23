

from tesla_powerwall import Powerwall

PowerWall = Powerwall("192.168.1.151")
PowerWall.login("coe123COE", "christian.olgaard@gmail.com")
print(PowerWall.is_authenticated())
print(PowerWall.get_charge())
print(PowerWall.get_status())
print(PowerWall.get_grid_status())
meters = PowerWall.get_meters()





#print(PowerWall.run())
#print(PowerWall.stop())
#print(PowerWall.run())

print(PowerWall.get_charge())

print(PowerWall.get_sitemaster())

print(PowerWall.get_meters())

print(PowerWall.get_grid_status())
print(PowerWall.is_grid_services_active())

print(PowerWall.get_site_info())

#print(PowerWall.set_site_name(, site_name: str))

print(PowerWall.get_status())

print(PowerWall.get_device_type())
print(PowerWall.get_serial_numbers())
print(PowerWall.get_operation_mode())

print(PowerWall.get_backup_reserve_percentage())
print(PowerWall.get_solars())

print(PowerWall.get_vin())

print(PowerWall.get_version())

print(PowerWall.detect_and_pin_version())


#print(PowerWall.pin_version(, vers: Union[str, version.Version]))


print(PowerWall.get_pinned_version())


print(PowerWall.get_api())


print(PowerWall.close())
#print(PowerWall.logout())