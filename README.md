# hass-sectoralarm

A Sector Alarm component for Home Assistant

## Usage

Clone or download the files, put them in your Home Assistant settings folder:

```
<your_home_assistant_folder>\custom_components\sector_alarm.py
<your_home_assistant_folder>\custom_components\sensor\sector_alarm.py
<your_home_assistant_folder>\custom_components\alarm_control_panel\sector_alarm.py
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
```

Skip optional lines completely if not wanted.