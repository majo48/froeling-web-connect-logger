# connect-web-logger
Scrape & log information from a registered account at connect-web.froeling.com.
Changes in the Fröling website may cause errors in this application, which is not synced with the website but fixed later on. 

# Prerequisites
- a Fröling PE1 pellet boiler at your home 
- a registered connect-web account at froeling.com which connects to your PE1 pellet boiler
- a computer (connected to the internet) capable of running this Python project periodically
  - See also file DEPENDENCIES.md

# Input (CLI / configuration)
- account name and password @connect-web.froeling.com
- data acquisition period in minutes (15, 30, 60)
- Copy file shared/local_settings.py.dist to shared/local_settings.py
- Edit shared/local_settings.py to match your configuration

# Process
- connect-web-logger/logger/app.py:
  - get status (configuration) data from the froeling website (read-only)
  - write status (configuration) values to a database
  - this project does NOT need MODBUS hardware (like https://github.com/mhoffacker/PyLamdatronicP3200)
- connect-web-logger/plotter/app.py:
  - render plots stored in the database 

# Output
- process status information (stdout, stderr)
- a SQLite database file containing the periodic data
  - is automatically recreated (empty) after a deletion
- four PNG plotter files (see Wiki/charts)

# Running the app
- change directory(cd) to where this project resides
- enter command: ***python3 -m logger username password period***
  - username: registered username at connect-web.froeling.com
  - password: registered password for the above user
  - period:   logging period in minutes (15, 30, 60)
  - w.o. arguments: the values are read from the configuration file
- enter command: ***python3 -m plotter***

# Fairness / Legal
- this app puts some strain on the froeling.com website
- please use only for optimizing your Fröling PE1 pellet boiler
- web scraping is legal for "intended usage" and for public data
  - reading your own "private" data is IMHO the same as reading public data (IANAL) 
  - see LICENSE file for more and detailed information
- Froeling, please provide a (local) LAN-API to the PE1 pellet boiler, avoiding the hassle of going thru the internet and the Fröling servers just to get some local data
  
  
