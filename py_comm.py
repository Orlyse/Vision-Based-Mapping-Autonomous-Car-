import time
import requests

ESP32_IP = "172.20.10.3"
MOTOR_URL = f"http://{ESP32_IP}/pwm"

def send_pwm(left, right):
    left = max(-255, min(255, int(left)))
    right = max(-255, min(255, int(right)))

    try:
        r = requests.get(MOTOR_URL, 
                        params={"L":left, "R":right}, 
                        timeout=2)
        
        print(f"Esp32 replied: {r.status_code} {r.text}")
    except Exception as e:
        print("Failed to send PWM:", e)

'''
while True:
    send_pwm(200, 220)
    time.sleep(0.2)
'''
