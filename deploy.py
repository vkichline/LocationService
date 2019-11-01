#!/bin/bash

sudo systemctl stop locationd

cp /var/cache/locationd/locationd.cache info/locationd.cache
sudo cp info/locationd.cache   /var/cache/locationd/locationd.cache
sudo cp info/locationd.service /etc/systemd/system/locationd.service
sudo cp locationd.py           /usr/local/lib/locationd/locationd.py
sudo cp astro.py               /usr/local/lib/locationd/astro.py
sudo cp DayCalc.py             /usr/local/lib/locationd/DayCalc.py
sudo cp TimeCalc.py            /usr/local/lib/locationd/TimeCalc.py 

sudo systemctl daemon-reload
sudo systemctl start locationd
