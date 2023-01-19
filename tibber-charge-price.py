import requests
import json
from datetime import datetime
import re

endpoint = "https://api.tibber.com/v1-beta/gql" # Set the GraphQL endpoint
api_key = "YOUR-TIBBER-API"
Domoticz_IP = "192.168.x.x"
Domoticz_Port = "8080"
Domoticz_IDX_chargeHours = "1194" 
Domoticz_IDX_customSensor = "1192" 
Domoticz_IDX_first_charge_price = "1195" # create General, Custom Sensor
Domoticz_IDX_current_price = "1196" # create General, Custom Sensor
Domoticz_IDX_charge_switch = "1245" # switch or function to enable charge
enable_currentsubscription = True # test function
headers = { # Set the headers including the API key and User-Agent
    "Authorization": f"Bearer {api_key}",
    "User-Agent": "testplugin/1.0"
}

# get the value of chargeHours from Domoticz
response = requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=devices&rid={Domoticz_IDX_chargeHours}')
data = response.json()
charge_level = data['result'][0]['Data']
match = re.search(r'\d+', charge_level)
chargeHours = int(match.group())/10
print("chargeHours:", chargeHours)

if enable_currentsubscription:
    query = """
    query {
      viewer {
        homes {
          currentSubscription {
            priceInfo {
              today {
                total
                startsAt
              }
            }
          }
        }
      }
    }
    """

response = requests.post(endpoint, json={'query': query}, headers=headers)

data = json.loads(response.text)

for home in data['data']['viewer']['homes']:
        if enable_currentsubscription:
            prices = [priceInfo['total'] for priceInfo in home["currentSubscription"]["priceInfo"]["today"]]
            prices_with_time = [(priceInfo['total'], priceInfo['startsAt']) for priceInfo in home["currentSubscription"]["priceInfo"]["today"]]
            prices_with_time.sort()
            charge_price = round(prices_with_time[int(chargeHours)-1][0], 3)
            first_charge_price = round(prices_with_time[0][0], 3)
            current_time = datetime.now().hour
            current_price = None
            for price in prices_with_time:
                if datetime.fromisoformat(price[1]).hour == current_time:
                    current_price = price[0]
                    break
            if current_price is None:
                current_price = prices[0]
            current_price = round(current_price,3)
            charge_price_time = datetime.fromisoformat(prices_with_time[int(chargeHours)-1][1]).strftime("%Y-%m-%d %H:%M:%S")
            print("charge_price:", charge_price, "at", charge_price_time)
            print("first_charge_price:", first_charge_price)
            print("current_price:", current_price)
            # Send the prices to Domoticz
            requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=udevice&idx={Domoticz_IDX_customSensor}&nvalue=0&svalue={charge_price}')
            requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=udevice&idx={Domoticz_IDX_first_charge_price}&nvalue=0&svalue={first_charge_price}')
            requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=udevice&idx={Domoticz_IDX_current_price}&nvalue=0&svalue={current_price}')
            # Enable switch
            if current_price <= first_charge_price:
                response = requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=switchlight&idx={Domoticz_IDX_chage_switch}&switchcmd=On')
            else:
                response = requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=switchlight&idx={Domoticz_IDX_chage_switch}&switchcmd=Off')
