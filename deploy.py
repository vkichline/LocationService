#!/bin/bash

echo Stopping locationd service
sudo systemctl stop locationd

echo Preserving/deploying locationd.cache
cp /var/cache/locationd/locationd.cache info/locationd.cache
sudo cp info/locationd.cache   /var/cache/locationd/locationd.cache

echo Deploying service control file
sudo cp info/locationd.service /etc/systemd/system/locationd.service

echo Deploying locationd content
# create directory if needed
sudo mkdir -p                  /usr/local/lib/locationd
sudo cp locationd.py           /usr/local/lib/locationd/locationd.py
sudo cp configuration.py       /usr/local/lib/locationd/configuration.py
sudo cp astro.py               /usr/local/lib/locationd/astro.py
sudo cp DayCalc.py             /usr/local/lib/locationd/DayCalc.py
sudo cp TimeCalc.py            /usr/local/lib/locationd/TimeCalc.py 

echo Reloading daemon cache
sudo systemctl daemon-reload
echo Restarting locationd service
sudo systemctl start locationd
echo Deployed
