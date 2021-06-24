import time
import json
import hashlib
from datetime import datetime
import requests

from requests_oauth2 import OAuth2BearerToken
import string
import random

import polyinterface
LOGGER = polyinterface.LOGGER

#import base64
# https://github.com/bismuthfoundation/TornadoWallet/blob/c4c902a2fe2d45ec399416baac4eefd39d596418/wallet/crystals/420_tesla/teslaapihandler.py#L219
class TeslaCloudAPI():

    def __init__(self, email, password):
        self.CLIENT_ID = "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
        self.CLIENT_SECRET = "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
        self.TESLA_URL = "https://owner-api.teslamotors.com"
        self.API = "/api/1"
        self.OPERATING_MODES = ["backup", "self_consumption", "autonomous"]
        self.TOU_MODES = ["economics", "balanced"]
        self.email = email
        self.password = password
        self.daysConsumption = {}
        self.tokeninfo = {}
        self.touScheduleList = []
        self.connectionEstablished = False

        self.products = {}
        self.site_id = ''
        #self.battery_id = ''
        if self.teslaCloudConnect(self.email, self.password): 
            self.connectionEstablished = True
            LOGGER.debug('site_status')
            self.site_status = self.teslaGetSiteInfo('site_status')
            LOGGER.debug('site_live')
            self.site_live = self.teslaGetSiteInfo('site_live')
            LOGGER.debug('site_info')
            self.site_info = self.teslaGetSiteInfo('site_info')
            LOGGER.debug('site_history_day')
            self.site_history = self.teslaGetSiteInfo('site_history_day')
            
            self.daysMeterSummary = self.teslaCalculateDaysTotals()
            self.touSchedule = self.teslaExtractTouScheduleList()
        else:
            return(None)
        #LOGGER.debug(self.site_info)    
        if 'tou_settings' in self.site_info:
            if 'optimization_strategy' in self.site_info['tou_settings']:
                self.touMode = self.site_info['tou_settings']['optimization_strategy']
            else:
                self.touMode = None
            if 'schedule' in self.site_info['tou_settings']:
                self.touScheduleList =self.site_info['tou_settings']['schedule']
            else:
                self.touScheduleList = []
        else:
            self.touMode = None
            self.touScheduleList = []
            LOGGER.debug('Tou mode not set')
        #self.battery_status = self.teslaGetBatteryInfo('bat_status') - not used any more 
        #self.battery_info = self.teslaGetBatteryInfo('bat_info') - not used anymore 

    def teslaUpdateCloudData(self, mode):
        if mode == 'critical':
            temp =self.teslaGetSiteInfo('site_live')
            if temp != None:
                self.site_live = temp
        elif mode == 'all':
            temp= self.teslaGetSiteInfo('site_live')
            if temp != None:
                self.site_live = temp
                
            temp = self.teslaGetSiteInfo('site_info')
            if temp != None:
                self.site_info = temp
            
            temp = self.teslaGetSiteInfo('site_history_day')            
            if temp != None:
                self.site_history = temp
        else:
            temp= self.teslaGetSiteInfo('site_live')
            if temp != None:
                self.site_live = temp
                
            temp = self.teslaGetSiteInfo('site_info')
            if temp != None:
                self.site_info = temp
            
            temp = self.teslaGetSiteInfo('site_history_day')            
            if temp != None:
                self.site_history = temp

            temp = self.teslaGetSiteInfo('site_status')
            if temp != None:
                self.site_status = temp


    def supportedOperatingModes(self):
        return( self.OPERATING_MODES )

    def supportedTouModes(self):
        return(self.TOU_MODES)

    def teslaCloudConnect(self, email, password):
        self.email = email
        self.password = password
        if self.site_id == '':
            try:
                products = self.teslaGetProduct()
                nbrProducts = products['count']
                for index in range(0,nbrProducts): #Can only handle one power wall setup - will use last one found
                    if 'resource_type' in products['response'][index]:
                        if products['response'][index]['resource_type'] == 'battery':
                            self.site_id ='/'+ str(products['response'][index]['energy_site_id'] )
                            self.products = products['response'][index]
                return(True)
            except:
                return(False)
        else:
            return(True)


    def __teslaGetToken(self):
        if self.tokeninfo:
            dateNow = datetime.now()
            tokenExpires = datetime.fromtimestamp(self.tokeninfo['created_at'] + self.tokeninfo['expires_in']- 100)
            if dateNow > tokenExpires:
                LOGGER.debug('Renewing token')
                self.tokeninfo = self.__tesla_connect(self.email, self.password)
        else:
            LOGGER.debug('Getting New Token')
            self.tokeninfo = self.__tesla_connect(self.email, self.password)
        return(self.tokeninfo)


    def __teslaConnect(self):
        return(self.__teslaGetToken())




    def teslaGetProduct(self):
        S = self.__teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.get(self.TESLA_URL + self.API + "/products")
                products = r.json()
                return(products)        
            except:
                LOGGER.debug('Error getting product info')
                return(None)



    def teslaSetOperationMode(self, mode):
        if self.connectionEstablished:
            S = self.__teslaConnect()
            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])          
                    if mode  in self.OPERATING_MODES:
                        payload = {'default_real_mode': mode}
                        r = s.post(self.TESLA_URL +  self.API+ '/energy_sites'+self.site_id +'/operation', json=payload)        
                        site = r.json()
                        if site['response']['code'] <210:
                            self.site_info['default_real_mode'] = mode
                            return (True)
                        else:
                            return(False)
                    else:
                        return(False)
                        #site="wrong mode supplied" + str(mode)
                    #LOGGER.debug(site)        
                except:
                    LOGGER.debug('Error setting operation mode')
                    return(False)
        else:
            return(False)

    def teslaExtractOperationMode(site_info):
        return(site_info['default_real_mode'])

    def teslaGetSiteInfo(self, mode):
        if self.connectionEstablished:

            S = self.__teslaConnect()
            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])            
                    if mode == 'site_status':
                        r = s.get(self.TESLA_URL + self.API+ '/energy_sites'+self.site_id +'/site_status')          
                        site = r.json()
                    elif mode == 'site_live':
                        r = s.get(self.TESLA_URL + self.API+ '/energy_sites'+self.site_id +'/live_status')          
                        site = r.json()
                    elif mode == 'site_info':
                        r = s.get(self.TESLA_URL + self.API+ '/energy_sites'+self.site_id +'/site_info')          
                        site = r.json()            
                    elif mode == 'site_history_day':
                        r = s.get(self.TESLA_URL + self.API+ '/energy_sites'+self.site_id +'/history', json={'kind':'power', 'period':'day'}) 
                        site = r.json()                        
                    else:
                        #LOGGER.debug('Unknown mode: '+mode)
                        return(None)
                    return(site['response'])
                except:
                    LOGGER.debug('Error getting data' + str(mode))
                    LOGGER.debug('Trying to reconnect')
                    self.tokeninfo = self.__tesla_connect(self.email, self.password)
                    return(None)
        else:
            return(None)
        
    def teslaGetSolar(self):
        return(self.products['components']['solar'])


    def teslaSetStormMode(self, EnableBool):
        if self.connectionEstablished:

            S = self.__teslaConnect()
            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])
                    payload = {'enabled': EnableBool}
                    r = s.post(self.TESLA_URL +  self.API+ '/energy_sites'+self.site_id +'/storm_mode', json=payload)
                    site = r.json()
                    if site['response']['code'] <210:
                        self.site_info['user_settings']['storm_mode_enabled'] = EnableBool
                        return (True)
                    else:
                        return(False)
                except:
                    LOGGER.debug('Error setting storm mode')
                    return(False)
        else:
            return(False)

    
    def teslaExtractStormMode(self):
        if self.site_info['user_settings']['storm_mode_enabled']:
            return(1)
        else:
            return(0)


    def teslaSetBackoffLevel(self, backupPercent):
        if self.connectionEstablished:
            LOGGER.debug('teslaSetBackoffLevel ' + str(backupPercent))
            S = self.__teslaConnect()
            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])
                    if backupPercent >=0 and backupPercent <=100:
                        payload = {'backup_reserve_percent': backupPercent}
                        r = s.post(self.TESLA_URL +  self.API + '/energy_sites'+self.site_id +'/backup', json=payload)        
                        site = r.json()
                        if site['response']['code'] <210:
                            self.site_info['backup_reserve_percent'] = backupPercent
                            return (True)
                        else:
                            return(False)

                    else:
                        return(False)
                        #site="Backup Percent out of range 0-100:" + str(backupPercent)
                        #LOGGER.debug(site)   
                except:
                    LOGGER.debug('Error setting bacup percent')
                    return(False)
        else:
            return(False)


    def teslaExtractBackupPercent(self):
        return(self.site_info['backup_reserve_percent'])

    def teslaUpdateTouScheduleList(self, peakMode, weekdayWeekend, startEnd, time_s):
        indexFound = False
        try:
            if weekdayWeekend == 'weekend':
                days = set([6,0])
            else:
                days = set([1,2,3,4,5])

            if self.touScheduleList == None:
                self.touScheduleList = self.teslaExtractTouScheduleList()

            for index in range(0,len(self.touScheduleList)):
                if self.touScheduleList[index]['target']== peakMode and set(self.touScheduleList[index]['week_days']) == days:
                    indexFound = True
                    if startEnd == 'start':
                        self.touScheduleList[index]['start_seconds'] = time_s
                    else:
                        self.touScheduleList[index]['end_seconds'] = time_s
            if not(indexFound):
                temp = {}
                temp['target']= peakMode
                temp['week_days'] = days
                if startEnd == 'start':
                    temp['start_seconds'] = time_s
                else:
                    temp['end_seconds'] = time_s
                self.touScheduleList.append(temp)
                indexFound = True
            return(indexFound)
        except:
            LOGGER.debug('Error updating schedule')
            return(False)

    def teslaSetTouSchedule(self, peakMode, weekdayWeekend, startEnd, time_s):
        if self.teslaUpdateTouScheduleList( peakMode, weekdayWeekend, startEnd, time_s):
            self.teslaSetTimeOfUse()

    def  teslaExtractTouTime(self, days, peakMode, startEnd ):
        indexFound = False
        try:
            if days == 'weekend':
                days =set([6,0])
            else:
                days = set([1,2,3,4,5])
            #data = set(self.touScheduleList[0]['week_days'])
            #LOGGER.debug(data == days)
            #LOGGER.debug(self.touScheduleList[0]['target']== peakMode)
            for index in range(0,len(self.touScheduleList)):
                if self.touScheduleList[index]['target']== peakMode and set(self.touScheduleList[index]['week_days']) == days:
                    if startEnd == 'start':
                        value = self.touScheduleList[index]['start_seconds']
                    else:
                        value = self.touScheduleList[index]['end_seconds']
                    indexFound = True
                    return(value)
            if not(indexFound):       
                self.site_info = self.teslaGetSiteInfo('site_info')
                self.touScheduleList = self.teslaExtractTouScheduleList()
                for index in range(0,len(self.touScheduleList)):
                    if self.touScheduleList[index]['target']== peakMode and set(self.touScheduleList[index]['week_days']) == days:
                        if startEnd == 'start':
                            value = self.touScheduleList[index]['start_seconds']
                        else:
                            value = self.touScheduleList[index]['end_seconds']
                        indexFound = True
                        return(value)
            if not(indexFound): 
                LOGGER.debug('No schedule appears to be set')            
                return(-1)
        except:
            LOGGER.error('No schedule idenfied')
            return(-1)


    def teslaSetTimeOfUseMode (self, touMode):
        self.touMode = touMode
        self.teslaSetTimeOfUse()



    def teslaSetTimeOfUse (self):
        if self.connectionEstablished:
            temp = {}
            S = self.__teslaConnect()
            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])
                    temp['tou_settings'] = {}
                    temp['tou_settings']['optimization_strategy'] = self.touMode
                    temp['tou_settings']['schedule'] = self.touScheduleList
                    payload = temp
                    r = s.post(self.TESLA_URL +  self.API+ '/energy_sites'+self.site_id +'/time_of_use_settings', json=payload)
                    site = r.json()
                    if site['response']['code'] <210:
                        self.site_info['tou_settings']['optimization_strategy'] = self.touMode
                        self.site_info['tou_settings']['schedule']= self.touScheduleList
                        return (True)
                    else:
                        return(False)
                except:
                    LOGGER.debug('Error setting time of use parameters')
                    return(False)
        else:
            return(False)


    def teslaExtractTouMode(self):
        return(self.site_info['tou_settings']['optimization_strategy'])

    def teslaExtractTouScheduleList(self):
        self.touScheduleList = self.site_info['tou_settings']['schedule']
        return( self.touScheduleList )

    def teslaExtractChargeLevel(self):
        return(round(self.site_live['percentage_charged'],2))
        
    def teslaExtractBackoffLevel(self):
        return(round(self.site_info['backup_reserve_percent'],1))

    def teslaExtractGridStatus(self): 
        return(self.site_live['island_status'])


    def teslaExtractSolarSupply(self):
        return(self.site_live['solar_power'])

    def teslaExtractBatterySupply(self):     
        return(self.site_live['battery_power'])

    def teslaExtractGridSupply(self):     
        return(self.site_live['grid_power'])

    def teslaExtractLoad(self): 
        return(self.site_live['load_power'])

    def teslaExtractGeneratorSupply (self):
        return(self.site_live['generator_power'])



    def teslaCalculateDaysTotals(self):
        try:
            data = self.site_history['time_series']
            nbrRecords = len(data)
            index = nbrRecords-1
            dateStr = data[index]['timestamp']
            Obj = datetime.strptime(dateStr, "%Y-%m-%dT%H:%M:%S%z")

            solarPwr = 0
            batteryPwr = 0
            gridPwr = 0
            gridServicesPwr = 0
            generatorPwr = 0
            loadPwr = 0

            prevObj = Obj
            while ((prevObj.day == Obj.day) and  (prevObj.month == Obj.month) and (prevObj.year == Obj.year) and (index >= 1)):

                lastDuration =  prevObj - Obj
                timeFactor= lastDuration.total_seconds()/60/60
                solarPwr = solarPwr + data[index]['solar_power']*timeFactor
                batteryPwr = batteryPwr + data[index]['battery_power']*timeFactor
                gridPwr = gridPwr + data[index]['grid_power']*timeFactor
                gridServicesPwr = gridServicesPwr + data[index]['grid_services_power']*timeFactor
                generatorPwr = generatorPwr + data[index]['generator_power']*timeFactor

                index = index - 1
                prevObj = Obj
                dateStr = data[index]['timestamp']
                Obj = datetime.strptime(dateStr, "%Y-%m-%dT%H:%M:%S%z")
            loadPwr = gridPwr + solarPwr + batteryPwr + gridServicesPwr + generatorPwr

            ySolarPwr = data[index]['solar_power']*timeFactor
            yBatteryPwr = data[index]['battery_power']*timeFactor
            yGridPwr = data[index]['grid_power']*timeFactor
            yGridServicesPwr = data[index]['grid_services_power']*timeFactor
            YGeneratorPwr = data[index]['generator_power']*timeFactor

            prevObj = Obj
            while ((prevObj.day == Obj.day) and  (prevObj.month == Obj.month) and (prevObj.year == Obj.year) and (index >= 1)):
                lastDuration =  prevObj - Obj
                timeFactor= lastDuration.total_seconds()/60/60
                ySolarPwr = ySolarPwr + data[index]['solar_power']*timeFactor
                yBatteryPwr = yBatteryPwr + data[index]['battery_power']*timeFactor
                yGridPwr = yGridPwr + data[index]['grid_power']*timeFactor
                yGridServicesPwr = yGridServicesPwr + data[index]['grid_services_power']*timeFactor
                YGeneratorPwr = YGeneratorPwr + data[index]['generator_power']*timeFactor

                index = index - 1
                prevObj = Obj
                dateStr = data[index]['timestamp']
                Obj = datetime.strptime(dateStr, "%Y-%m-%dT%H:%M:%S%z")

            yLoadPwr = yGridPwr + ySolarPwr + yBatteryPwr + yGridServicesPwr + YGeneratorPwr

            self.daysConsumption = {'solar_power': solarPwr, 'consumed_power': loadPwr, 'net_power':-gridPwr
                                ,'battery_power': batteryPwr ,'grid_services_power': gridServicesPwr, 'generator_power' : generatorPwr
                                ,'yesterday_solar_power': ySolarPwr, 'yesterday_consumed_power': yLoadPwr, 'yesterday_net_power':-yGridPwr
                                ,'yesterday_battery_power': yBatteryPwr ,'yesterday_grid_services_power': yGridServicesPwr, 'yesterday_generator_power' : YGeneratorPwr, }
        
            return(True)
        except:
            LOGGER.error(' Error obtaining time data')

        

    def teslaExtractDaysSolar(self):
        return(self.daysConsumption['solar_power'])
    
    def teslaExtractDaysConsumption(self):     
        return(self.daysConsumption['consumed_power'])

    def teslaExtractDaysGeneration(self):         
        return(self.daysConsumption['net_power'])

    def teslaExtractDaysBattery(self):         
        return(self.daysConsumption['battery_power'])

    def teslaExtractDaysGridServicesUse(self):         
        return(self.daysConsumption['grid_services_power'])

    def teslaExtractDaysGeneratorUse(self):         
        return(self.daysConsumption['generator_power'])  

    def teslaExtractYesteraySolar(self):
        return(self.daysConsumption['yesterday_solar_power'])
    
    def teslaExtractYesterdayConsumption(self):     
        return(self.daysConsumption['yesterday_consumed_power'])

    def teslaExtractYesterdayGeneraton(self):         
        return(self.daysConsumption['yesterday_net_power'])

    def teslaExtractYesterdayBattery(self):         
        return(self.daysConsumption['yesterday_battery_power'])

    def teslaExtractYesterdayGridServiceUse(self):         
        return(self.daysConsumption['yesterday_grid_services_power'])

    def teslaExtractYesterdayGeneratorUse(self):         
        return(self.daysConsumption['yesterday_generator_power'])  

    def teslaExtractOperationMode(self):         
        return(self.site_info['default_real_mode'])
    '''
    def teslaExtractConnectedTesla(self):       
        return(True)

    def teslaExtractRunning(self):  
        return(True)
    '''
    #???
    def teslaExtractPowerSupplyMode(self):  
        return(True)

    def teslaExtractGridServiceActive(self):
        if self.site_live['grid_services_active']: 
            return(1)
        else:
            return(0)




    '''
    --------------------------------------------------------------------------------------------------------------------------------------------------
    Followiung code taken from:
    https://github.com/bismuthfoundation/TornadoWallet/blob/c4c902a2fe2d45ec399416baac4eefd39d596418/wallet/crystals/420_tesla/teslaapihandler.py#L219
    '''
    def __tesla_connect(self,email, pwd):
        code_verifier = ''.join(random.choices(string.ascii_letters+string.digits, k=86))
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).hexdigest()

        data = {}
        data['client_id']='ownerapi'
        data['code_challenge']=code_challenge
        data['code_challenge_method']='S256'
        data['redirect_uri']='https://auth.tesla.com/void/callback'
        data['response_type']='code'
        data['scope']='openid email offline_access'
        data['state']='123'
        data['login_hint']=email

        r = requests.get('https://auth.tesla.com/oauth2/v3/authorize', data)
        cookies = r.cookies
        data = self.html_parse(data,r.text)
        data['identity'] = email
        data['credential'] = pwd

        r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=data, cookies=cookies, allow_redirects=False)
        code = self.myparse2(r.text,'code=')

        data = {}
        data['grant_type'] = 'authorization_code'
        data['client_id'] = 'ownerapi'
        data['code'] = code
        data['code_verifier'] = code_verifier
        data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
        r = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
        S = json.loads(r.text)

        data = {}
        data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
        data['client_id']=self.CLIENT_ID
        data['client_secret']=self.CLIENT_SECRET
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + '/oauth/token',data)
                S = json.loads(r.text)
            except:
                pass
		
        time.sleep(1)
        return S

    def myparse(self,html,search_string):
        L = len(search_string)
        i = html.find(search_string)
        j = html.find('"',i+L+1)
        return html[i+L:j]

    def myparse2(self,html,search_string):
        L = len(search_string)
        i = html.find(search_string)
        j = html.find('&',i+L+1)
        return html[i+L:j]

    def html_parse(self,data,html):
        data['_csrf'] = self.myparse(html,'name="_csrf" value="')
        data['_phase'] = self.myparse(html,'name="_phase" value="')
        data['_process'] = self.myparse(html,'name="_process" value="')
        data['transaction_id'] = self.myparse(html,'name="transaction_id" value="')
        return data