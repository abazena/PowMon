import yaml
import serial
import pathlib
from cryptography.fernet import Fernet
import time
import threading
import requests
import os
from threading import Lock
OKBLUE  = '\033[94m'
OKGREEN = '\033[92m'
OKCYAN = '\033[96m'
WARNING = '\033[93m'
FAIL = '\033[91m'
lock = Lock()

def update_conf():
    settings['EHOST'] = ""
    with open(settings['PROJECT_ROOT'] + "/settings.yaml", "w") as _file:
        yaml.dump(settings, _file)
def write_file(payload):
    try:
        path = settings['LOCAL_DATA_ROOT'] + settings['LOCAL_DATA_FILE']
        fsize = os.path.getsize(path)
        if(fsize >= settings['FILE_SIZE_LIMIT']):
            settings['LOCAL_DATA_FILE'] = "/" + str(time.time()).replace('.' , '') + "-data.csv"
            path = settings['LOCAL_DATA_ROOT'] + settings['LOCAL_DATA_FILE']
            update_conf()
        with open( path, "a+") as file_object:
            file_object.write(payload)
        return True
    except Exception as e:
        print(FAIL + '[ERROR]' + e)
        return False

def local_save(data):
    if(settings['SYNC_WRITE'] == True):
        with lock:
            return write_file(data)
    else:
        return write_file(data)
        

def log(sensor_id, payload, rstatus, sstatus):
    payload = payload.rstrip("\n")
    if(settings['LOG_LEVEL'] == 1):
        print(OKBLUE + "[DEBUG]\t" , sensor_id , "\t", rstatus, "\t" , sstatus)
    elif(settings['LOG_LEVEL'] == 2):
        print(OKBLUE +"[DEBUG]\t" ,payload)
    elif(settings['LOG_LEVEL'] == 3):
        print(OKBLUE +"[DEBUG]\t" , sensor_id , "\t", rstatus, "\t" , sstatus, "\t" ,payload)

def remote_save(payload):
    r = requests.post(settings['EHOST'], data=payload)
    return r.status_code

def flush(arduino):
    arduino.write(str.encode('r \n'))
    arduino.readline()[:-2]
    time.sleep(0.001)
    arduino.write(str.encode('r \n'))
    arduino.readline()[:-2]

def read_serial(sensor):
    try:
        arduino = serial.Serial(sensor['PORT'],settings['BUDRATE'],timeout=settings['TIMEOUT'])
        time.sleep(1)
        flush(arduino)
        while True:
            arduino.write(str.encode('read \n'))
            time.sleep(0.001) 
            unix_ts = str(time.time()).replace('.' , '')
            data = arduino.readline()[:-2].decode("utf-8")
            if data: 
                try:
                    voltage = float(data) * settings['VPP']
                    # voltage -= settings['OFFSET']
                    amps = "{:.4f}".format(voltage / settings['SNS'])
                    if(voltage / settings['SNS'] > 10):
                        tmp = "000"
                        payload = str(unix_ts) + "," + sensor['SENSORS_ID'] + "," + tmp + "," +  tmp + "," +tmp+"\n"
                    else:
                        payload = str(unix_ts) + "," + sensor['SENSORS_ID'] + "," + data + "," +  "{:.2f}".format(voltage) + "," +str(amps)+"\n"
                    sstatus = local_save(payload)
                    rstatus = remote_save(payload)
                    if(settings['LOG_LEVEL'] > 0):
                        log(sensor['SENSORS_ID'],payload,rstatus,sstatus)
                except Exception as e:
                    print(FAIL + '[ERROR]' + e)
            flush(arduino)
    except Exception as e:
        print(WARNING + "[WARNING] attempting to connect to" , sensor['SENSORS_ID'] , e)
        time.sleep(5)
        read_serial(sensor)

if __name__ == "__main__":
    print(OKGREEN + "[INFO] Starting PowMonDataCollector")
    print(OKGREEN +"[INFO] Loading Settings")
    with open(str(pathlib.Path(__file__).parent.absolute()) + "/settings.yaml", 'r') as stream:
        settings = yaml.safe_load(stream)
    settings['EHOST'] = Fernet(str.encode(settings['LOCAL_DATA_PATH'])).decrypt(str.encode(settings['HOST'])).decode()
    print(OKCYAN +'[Settings]\tFILE_SIZE_LIMIT = ' , settings['FILE_SIZE_LIMIT'] , '\tLOG_LEVEL = ' , settings['LOG_LEVEL'] , '\tSYNC_WRITE =' , settings['SYNC_WRITE'])
    for sensor in settings['SENSORS']:
        print(OKGREEN +"[INFO] Starting thread: " , sensor['SENSORS_ID'])
        x = threading.Thread(target=read_serial, args=(sensor,))
        x.start()
        print(OKGREEN +"[INFO] Started thread: " , sensor['SENSORS_ID'])