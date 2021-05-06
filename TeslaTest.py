
import time
import json
import os
from tesla_powerwall import Powerwall

#from TeslaInfo import tesla_info
#from  ISYprofile import isyHandling
from datetime import date
'''
dayInfo = date.today()
solar = 100
generation = 1000
consumption = 10
filename = 'testFile.txt'
for i in range(100):
    if not(os.path.exists('./dailyData')):
        os.mkdir('./dailyData')
    dataFile = open('./dailyData/'+filename, 'a')
    #print('Date,'+str(dayInfo)+ ','+'solarKW,'+str(solar)+',ConsumptionKW,'+str(consumption)+',Generation,'+str(generation)+'\n')
    dataFile.write('Date,'+str(dayInfo)+ ','+'solarKW,'+str(solar)+',ConsumptionKW,'+str(consumption)+',Generation,'+str(generation)+'\n')
    dataFile.close()
    solar = solar + i
    consumption = consumption+ i
    generation = generation + i

'''
drivers = []
PowerWall = Powerwall("192.168.1.151")
temp = PowerWall.login( 'coe123COE', 'christian.olgaard@gmail.com')
print(PowerWall.is_authenticated())
PowerWall.close()
controllerName = 'powerwall'
id = 'tpwid'
TPW = tesla_info("192.168.1.151", "coe123COE", "christian.olgaard@gmail.com", controllerName, id)
ISYparams = TPW.supportedParamters(id)
for key in ISYparams:
    test = ISYparams[key]
    if  test != {}:
        val = TPW.getISYvalue(key, id)
        print(test['systemVar'] + ' : '+ str(val))
        
        drivers.append({'driver':key, 'value':val, 'uom':test['uom'] })
print()


for i in range(100):
    for key in ISYparams:
        test = ISYparams[key]
        if  test != {}:
            val = TPW.getISYvalue(key, id)
            print(test['systemVar'] + ' : '+ str(val))
    time.sleep(60)
    TPW.pollSystemData()
    print('\nineration : ' + str(i))


        #LOGGER.debug# LOGGER.debug(  'driver:  ' +  temp['driver'])

#self.teslaInfo = tesla_info('192.168.1.151', 'coe123COE', 'christian.olgaard@gmail.com')
print(PowerWall.is_authenticated())
#print(PowerWall.get_charge())
#print(PowerWall.get_status())
#print(PowerWall.get_grid_status())
metersOld = PowerWall.get_meters()
#time.sleep(60)

for i in range(3):
    meters = PowerWall.get_meters()
    print(meters.solar.instant_power,meters.solar.energy_exported, meters.solar.energy_imported, meters.solar.last_communication_time )
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
print (test1)
print('\nget sitemaster ' )
test2 = PowerWall.get_sitemaster() #Needed


print(test2.is_connected_to_tesla, test2.is_running, test2.status)
print('\n get Meters ' )
#print( PowerWall.get_meters())

print('\n get grid status ' ) # Needed
test3 = PowerWall.get_grid_status() # Needed
print(test3)

print('\n get grid services active ')
test4 = PowerWall.is_grid_services_active() # Needed
print(test4)

print('\n get operation mode ')
test5 = PowerWall.get_operation_mode()
print(test5)

print('\n get site info ')
test6 = PowerWall.get_site_info()
print(test5)

#print(PowerWall.set_site_name(, site_name: str))

print('\n get status ')
test7 = PowerWall.get_status() # NEeded
print(test7)
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