import network
from microdot_asyncio import Microdot, Response
from microdot_asyncio_websocket import with_websocket
import json
from servo import Servo
import _thread
from hcsr04 import HCSR04
import time


ssid="SSID"
password="PASSWORD"
mode = 3 # WPA2

html="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <div class="main">
        <div><input type="button" value="ON" id="on"></div>
        <div><input type="button" value="OFF" id="off"></div>
    </div>
    <script>
        websock = new WebSocket('ws://' + window.location.hostname + '/ws');
        on = document.querySelector("#on")
        off = document.querySelector("#off")
        on.addEventListener("click", function (e) {
            websock.send(JSON.stringify("ON"));   
        });
        
        off.addEventListener("click", function (e) {
            websock.send(JSON.stringify("OFF"));   
            });
            
        websock.onmessage = function(evt) {
            recvd_data = JSON.parse(evt.data)
            if(recvd_data=="On"){
                on.style.color="red";
                off.style.color="green";
            }
            else if(recvd_data=="Off"){
                off.style.color="red";
                on.style.color="green";
            }
            };
    </script>
</body>
</html>
"""
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

#print(station.ifconfig())
servo=Servo(pin=13)


# Thread running on core 0
def Sensor():
    sensor = HCSR04(trigger_pin=12, echo_pin=14, echo_timeout_us=10000)
    while True:
         distance = sensor.distance_cm()
         #print('Distance:', distance, 'cm')
         
         if distance <=46 and distance >=37:
            time.sleep_ms(500)
            distance = sensor.distance_cm()      
            if distance <=46 and distance >=37:
                servo.move(0)
                print("OFF!")         
         elif distance <=6:
             servo.move(41)
             print("Open!")
            
# Thread running on core 1
app = Microdot()
@app.get('/')
def index(req):
    return Response(body=html, headers={'Content-Type': 'text/html'})

@app.route('/ws')
@with_websocket
async def websock(request,ws):
    while True:
        recv_data = await ws.receive()
        data = json.loads(recv_data)

        if data=="ON":
            servo.move(41)   
            await ws.send(json.dumps("On"))
        elif data=="OFF":
            servo.move(0)
            await ws.send(json.dumps("Off"))

        
_thread.start_new_thread(Sensor,())
app.run(host="0.0.0.0",port=80)
