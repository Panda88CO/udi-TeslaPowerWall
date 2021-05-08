# UDI Polyglot v2 Tesla Power Wall 2

[![license]( MIT 3 license - see license file)

Utilizes https://github.com/jrester/tesla_powerwall API (not official Tesla API - MIT license)

This Poly provides an interface between Tesla Power and system and [Polyglot v2](https://github.com/UniversalDevicesInc/polyglot-v2) server.

### Overview
ShortPoll updates critical data and  heartbeat
Long poll updates for all data.  
Daily Totals are logged to file in directory dailyData
Need to specify IPaddress, tesla login email and password
More data could easily be made available if needed


### Installation instructions
Make sure that you have a `zip` executable on the system, install using your OS package manager if necessarily.
You can install NodeServer from the Polyglot store or manually running
```
cd ~/.polyglot/nodeservers
git clone https://github.com/Panda88CO/udi-TeslaPowerWall.git udi-TeslaPOwerWall
cd udi-TeslaPowerWall
./install.sh
``` 


### Notes


Thanks and good luck.

