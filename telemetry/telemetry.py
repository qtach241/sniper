import sys
import getopt
import logging
import os
import socket
import threading
import time
import pprint

usage_text = "Usage: telemetry.py -e <exchange> -s <symbol>"

symbol = ""
exchange = ""

opts, args =  getopt.getopt(sys.argv[1:], "s:U:u:",["--help"])
for opt, arg in opts:
    if opt == '-e':
        exchange = arg
    elif opt in ("-s"):
        symbool = arg
    elif opt in ("--help"):
        print(usage_text)
        sys.exit()

def thread_loop():
    while True:
        print("hello from thread!")
        time.sleep(1)

thread = threading.Thread(target=thread_loop, args=())
thread.daemon = True
thread.start()
		
while True:
	print("hello from main loop!")
	time.sleep(5)

thread.join()
