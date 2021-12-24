import subprocess
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt
from sense_hat import SenseHat

sense = SenseHat()
sense.low_light = True
sense.clear()


def print_green():
    sense.set_pixel(3, 2, (0, 255, 0))
    sense.set_pixel(4, 2, (0, 255, 0))
    sense.set_pixel(5, 3, (0, 255, 0))
    sense.set_pixel(5, 4, (0, 255, 0))
    sense.set_pixel(4, 5, (0, 255, 0))
    sense.set_pixel(3, 5, (0, 255, 0))
    sense.set_pixel(2, 4, (0, 255, 0))
    sense.set_pixel(2, 3, (0, 255, 0))


def print_red():
    sense.set_pixel(3, 2, (255, 0, 0))
    sense.set_pixel(4, 2, (255, 0, 0))
    sense.set_pixel(5, 3, (255, 0, 0))
    sense.set_pixel(5, 4, (255, 0, 0))
    sense.set_pixel(4, 5, (255, 0, 0))
    sense.set_pixel(3, 5, (255, 0, 0))
    sense.set_pixel(2, 4, (255, 0, 0))
    sense.set_pixel(2, 3, (255, 0, 0))


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK Returned code=", rc)
        print_green()

    else:
        print("Bad connection Returned code=", rc)
        print_red()


def on_disconnect(client, userdate, rc):
    print("Disconnected. Return Code: ", rc)
    print_red()


def on_publish(client, obj, mid):
    print("Message ID: " + str(mid))
    sense.clear()
    for x in range(8):
        sense.set_pixel(4, x, (0, 0, 255))
        sense.set_pixel(3, x, (0, 0, 255))

        time.sleep(0.2)
    sense.clear()
    print_green()


client_id = f'python-mqtt-{random.randint(0, 1000)}'
mqttc = mqtt.Client(client_id, clean_session=True,
                    userdata=None, transport="websockets")

mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_disconnect = on_disconnect

mqttc.tls_set()
mqttc.connect('mqtt.huckcity.ie', 9001)
mqttc.loop_start()

mac_address_store = {}


def get_mac_addresses():
    print('Scanning...')
    # Retrive NMAP MAC address listings
    scan = subprocess.check_output(
        "sudo nmap -sn -R 192.168.1.0/24 | awk '/MAC Address:/{print $3}' | sort ", shell=True)

    # Split scan output line break and pop last entry due to trailing \n
    scan_result = scan.decode().split('\n')
    scan_result.pop()

    # Set up key value pars with timestamp
    mac_addresses = {}
    for addr in scan_result:
        mac_addresses[addr] = datetime.now()
    return mac_addresses


def update_log(msg):
    f = open("output.txt", "a")
    f.write(msg)
    f.write('\n')
    f.close()


def publish_update(addr, state):
    # publish device mac address and state(online/offline)
    mqttc.publish("macstatus/"+addr, str(state), qos=2)


# Infinte loop to run an NMAP scan every 60 seconds
while True:
    # We can't change dictionary size while iterating, so
    # we'll save keys to be added/removed from the store here
    to_pop = []
    to_push = []

    # If mac address store is empty it's the first time running so just scan
    if not mac_address_store:
        mac_address_store = get_mac_addresses()

    # otherwise, scan for an updated list to compare the two every 60 seconds
    else:
        # Compare
        new_mac_addresses = get_mac_addresses()

        for k, v in mac_address_store.items():
            if k in new_mac_addresses:
                datediff = new_mac_addresses[k] - mac_address_store[k]
                if datediff.seconds > 300:
                    print(f'{k} is still online')
                    update_log(k + ' went offline at ' +
                               datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                    publish_update(k, True)

            else:
                print(f'{k} has gone offline!')
                to_pop.append(k)
                update_log(k + ' went offline at ' +
                           datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                publish_update(k, False)

        for k, v in new_mac_addresses.items():
            if k not in mac_address_store:
                to_push.append(k)
                print(f'{k} has joined the network!')
                update_log(k + ' joined the network at ' +
                           datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                publish_update(k, True)

        # pop/push any items as required
        if to_pop:
            for key in to_pop:
                mac_address_store.pop(key)
        if to_push:
            for key in to_push:
                mac_address_store[key] = datetime.now()

    print('Sleeping...')
    time.sleep(60)
