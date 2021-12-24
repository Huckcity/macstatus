#!/bin/bash

IP_ARRAY=( `nmap -sn 192.168.1.0/24 | grep "Nmap scan report" | awk '{print $NF}'` )
printf IP_ARRAY