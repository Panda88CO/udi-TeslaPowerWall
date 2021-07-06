# udi-powerwall
## Power wall Node server
The main node displays data - setup node allows configuration of different parameters
For the setup node to show one need to connect to the cloud (Tesla only allows changes via cloud)
Note - there is a discrepancy between local and cloud back-off limt.  Local power wall reports about 3% higher than the value specified perventage in the cloud (one can only change back-f value via the cloud or Tesla App)

## Code
Code uses API (local power wall) from https://github.com/jrester/tesla_powerwall API - not official Tesla API 
Also uses code taken from: https://github.com/bismuthfoundation/TornadoWallet/blob/c4c902a2fe2d45ec399416baac4eefd39d596418/wallet/crystals/420_tesla/teslaapihandler.py#L219 for OAUTH on Tesla cloud data.  Added code for more efficient Token refresh
Code is under MIT license.
Some info on the clould API can be found at https://tesla-api.timdorr.com/

## Installation
To run node server user must first select data source - from Local Power Wall and/or Tesla Cloud.   Local is not working on polyglot cloud.  
 
Configuration requires 2 steps first time:
#### 1) First user needs to sepcifiy source of data (LOCAL/CLOUD/BOTH) 
#### 2) Restart node
#### 3) Next user will speficy the needed user IDs and passwords for the selected option  (and local Tesla power wall IP address if chosen).  
#### 4) Resrtart
## Notes 
Using cloud access user can set all parameters mobile app currently supports (except car charging limit).

Generator support is not tested (I do not have one) and I have not tested without solar connected.

An option to generate a daily log file is included - file must be down loaded separately from polisy/polyglot - CSV formatted data".  Disabled by default.