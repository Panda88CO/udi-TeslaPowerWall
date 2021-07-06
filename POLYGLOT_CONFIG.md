# udi-powerwall

## Installation
To run node server user must first select data sources - from Local Power Wall (LOCAL),  Tesla Cloud(CLOUD) or both (BOTH).   Polyglot cloud requires CLOUD connection and will not allow LOCAL.  
Cloud account is needed if ISY is to make changes to Tesla Power Wall - e.g. only enable storm mode when not in peak hours, or control when to use the battery (vs using Tesla's predefined algorithms)

### Polisy/ local Polyglot
Configuration requires 4 steps first time (Polisy/Polyglot - non cloud):
#### 1) First user needs to sepcifiy source of data (LOCAL/CLOUD/BOTH) 
#### 2) Restart node
#### 3) Next user will speficy the needed user IDs and passwords for the selected option  (and local Tesla power wall IP address if chosen).  
#### 4) Restart

### Polyglot cloud
#### 1) Enter email and password for cloud account using CLOUD_USER_EMAIL and CLOUD_USER_PASSWORD keywords 
#### 2) Stop
#### 3) Start aand wait 2-3min

## Notes 
LOGFILE can be used to generate a daily summary file (csv) in dailyData directory - File must be downloaded with separate tool for now.
