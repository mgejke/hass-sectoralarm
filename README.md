# hass-sectoralarm

A Sector Alarm component for Home Assistant

## Usage

Clone or download the files, put them in your Home Assistant settings folder:

```
<your_home_assistant_folder>\custom_components\sector_alarm\__init__.py
<your_home_assistant_folder>\custom_components\sector_alarm\sensor.py
<your_home_assistant_folder>\custom_components\sector_alarm\alarm_control_panel.py
```

Add the following to your settings file:
```
sector_alarm:
  email: youremail@something.com
  password: *******
  alarm_id: <can be found from the url when you login to Sector Alarm, inside "">
  code: <Your pin code to asm/disarm, optional>
  thermometers: <if any thermometers should be added to HA, true/false, default is true>
  alarm_panel: <if the alarm panel component should be added to HA, true/false, default is true>
  version: <version of the sector alarm api, default is 'v1_1_76', set to 'auto' for automatic detection>
```

Skip optional lines completely if not wanted.
