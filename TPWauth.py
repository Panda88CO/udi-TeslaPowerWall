import time
import json
import hashlib
from datetime import datetime
import requests

from requests_oauth2 import OAuth2BearerToken
import string
import random
import captcha

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    PG_CLOUD_ONLY = True  

LOGGER = polyinterface.LOGGER  
    
class TPWauth:
    def __init__(self, email, password):
        self.code_verifier = ''.join(random.choices(string.ascii_letters+string.digits, k=86))   
        self.code_challenge = hashlib.sha256(self.code_verifier.encode('utf-8')).hexdigest()
        self.email = email
        self.password = password
        self.captchaAPIKEY = captcha_APIKEY
        self.state_str = 'ThisIsATest' 
        self.cookies = None
        self.data = {}
        self.captchaMethod = 'AUTO'
        #self.captchaMethod = 'EMAIL'
        '''
        headers = {
        'User-Agent': 'PowerwallDarwinManager',
        'x-tesla-user-agent': '' ,
        'X-Requested-With': 'com.teslamotors.tesla',
        }
        '''
        self.headers = {'User-Agent' : 'PowerwallDarwinManager'  }
        self.__tesla_initConnect(self.email, self.password)



    def __tesla_refresh_token(self):
        data = {}
        data['grant_type'] = 'refresh_token'
        data['client_id'] = 'ownerapi'
        data['refresh_token']=self.Rtoken
        data['scope']='openid email offline_access'      
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
            except  Exception as e:
                LOGGER.debug('Exception __tesla_refersh_token: ' + str(e))
                pass
        
        time.sleep(1)
        self.S = S
        return S


    '''
    --------------------------------------------------------------------------------------------------------------------------------------------------
    Following code originates from:
    https://github.com/bismuthfoundation/TornadoWallet/blob/c4c902a2fe2d45ec399416baac4eefd39d596418/wallet/crystals/420_tesla/teslaapihandler.py#L219
    but has been modified to support token renew and support captcha extranction 
    '''



    def __tesla_initConnect(self, email, pwd):
        self.data = {}
        self.data['audience'] = ''
        self.data['client_id']='ownerapi'
        self.data['code_challenge']=self.code_challenge
        self.data['code_challenge_method']='S256'
        self.data['redirect_uri']='https://auth.tesla.com/void/callback'
        self.data['response_type']='code'
        self.data['scope']='openid email offline_access'
        self.data['state']=self.state_str
        self.data['login_hint']=self.email
        r = requests.get('https://auth.tesla.com/oauth2/v3/authorize',  self.data)
        self.cookies = r.cookies
        self.data = self.html_parse(self.data,r.text)
        self.data['identity'] = email
        self.data['credential'] = pwd
        self.captchaFile = captcha.getCaptcha(self.headers, self.cookies)
        if self.captchaMethod == 'EMAIL':
            captcha.sendEmailCaptcha(self.captchaFile, self.email)
        

    def tesla_connect(self, captchaCode, captchaMethod, captchaAPIKey ):
        if captchaMethod == 'AUTO': 
            captchaCode = captcha.solveCaptcha(self.captchaFile, captchaAPIKey )
        self.data['captcha'] =  captchaCode    
        r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=self.data, cookies=self.cookies, headers=self.headers, allow_redirects=False)

        while "Captcha does not match" in r.text:
            if self.captchaMethod == 'EMAIL':
                #LOGGER.debug('Captcha not correct - try to restart node server - captcha = ' + captchaCode)
                return(None)          
            else:
                captchaFile = captcha.getCaptcha(self.headers, self.cookies)
                captchaCode = captcha.solveCaptcha(captchaFile, self.captchaAPIKEY)
                data['captcha'] =  captchaCode  
                r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=self.data, cookies=self.cookies, headers=self.headers, allow_redirects=False)

        while r.status_code != 302 and count < 5:
            time.sleep(1)
            count = count + 1
            r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=self.data, cookies=self.cookies, headers=self.headers, allow_redirects=False)   
    
        code = self.myparse2(r.text,'code=')

        data = {}
        data['grant_type'] = 'authorization_code'
        data['client_id'] = 'ownerapi'
        data['code'] = code
        data['code_verifier'] = self.code_verifier
        data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
        r = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
        S = json.loads(r.text)
        if 'refresh_token' in S:
            self.Rtoken = S['refresh_token']
        else:
            self.Rtoken = None

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


    def __tesla_connect(self,email, pwd):
        #code_verifier = ''.join(random.choices(string.ascii_letters+string.digits, k=86))
        #code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).hexdigest()
        state_str = 'ThisIsATest' #Random string
        '''
        headers = {
        'User-Agent': 'PowerwallDarwinManager',
        'x-tesla-user-agent': '' ,
        'X-Requested-With': 'com.teslamotors.tesla',
        }
        '''

        #self.headers = {'User-Agent' : 'PowerwallDarwinManager'  }
        #r = req.get('https://auth.tesla.com/oauth2/v3/authorize', headers=headers )
        data = {}
        data['audience'] = ''
        data['client_id']='ownerapi'
        data['code_challenge']=self.code_challenge
        data['code_challenge_method']='S256'
        data['redirect_uri']='https://auth.tesla.com/void/callback'
        data['response_type']='code'
        data['scope']='openid email offline_access'
        data['state']=self.state_str
        data['login_hint']=self.email

        r = requests.get('https://auth.tesla.com/oauth2/v3/authorize',  data)
        self.cookies = r.cookies
        data = self.html_parse(data,r.text)
        data['identity'] = email
        data['credential'] = pwd
        #data['cancel'] = ''
        #data['_process'] = '1'
        #data['_phase'] = 'authenticate'
        captchaOK = False
        while not(captchaOK):
            captchaFile = captcha.getCaptcha(self.headers, self.cookies)
            captcha.sendEmailCaptcha(captchaFile, email)
            captchaCode = captcha.solveCaptcha(captchaFile, self.captchaAPIKEY)

            #print(captchaCode)
            data['captcha'] =  captchaCode
            r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=data, cookies=self.cookies, headers=self.headers, allow_redirects=False)
            if "Captcha does not match" in r.text:
                captchaOK = False
            else:
                captchaOK = True
                count = 0
                while r.status_code != 302 and count < 5:
                    time.sleep(1)
                    count = count + 1
                    r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=data, cookies=self.cookies, headers=self.headers, allow_redirects=False)   
        
        code = self.myparse2(r.text,'code=')

        data = {}
        data['grant_type'] = 'authorization_code'
        data['client_id'] = 'ownerapi'
        data['code'] = code
        data['code_verifier'] = self.code_verifier
        data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
        r = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
        S = json.loads(r.text)
        if 'refresh_token' in S:
            self.Rtoken = S['refresh_token']
        else:
            self.Rtoken = None

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
        LOGGER.debug('Oauth 1: ' + str(r.cookies))
        cookies = r.cookies
        data = self.html_parse(data,r.text)
        data['identity'] = email
        data['credential'] = pwd

        r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=data, cookies=cookies, allow_redirects=False)

        code = self.myparse2(r.text,'code=')
        LOGGER.debug('Oauth 2: ' +str(code))
        data = {}
        data['grant_type'] = 'authorization_code'
        data['client_id'] = 'ownerapi'
        data['code'] = code
        data['code_verifier'] = code_verifier
        data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
        r = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
        S = json.loads(r.text)
        LOGGER.debug('Oauth 3: ' + str(S))
        if 'refresh_token' in S:
            self.Rtoken = S['refresh_token']
        else:
            self.Rtoken = None
            LOGGER.debug('Oauth 3a: No Rtoken' )
        data = {}
        data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
        data['client_id']=self.CLIENT_ID
        data['client_secret']=self.CLIENT_SECRET
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + '/oauth/token',data)
                S = json.loads(r.text)
                LOGGER.debug('Oauth 4: ' + str(S))
            except  Exception as e:
                LOGGER.debug('Exception __tesla_connect: ' + str(e))
                pass
        
        time.sleep(1)
        return S
    '''

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