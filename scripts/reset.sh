#!/bin/bash

sudo rm -rf /root/raspberrystem_projects/*
sudo find /home/pi/rstem/projects/demos -name *.py -exec cp {} /root/raspberrystem_projects \;
sudo find /home/pi/rstem/projects/demos -name *.spr -exec cp {} /root/raspberrystem_projects \;

