import requests
import json
from datetime import datetime
import re

endpoint = "https://api.tibber.com/v1-beta/gql" # Set the GraphQL endpoint
api_key = "API-KEY" # get your own api from developer.tibber.com
Domoticz_IP = "192.168.x.x" # your domoticz ip
Domoticz_Port = "8080" #your domoticz port
Domoticz_IDX_chargeHours = "1194" # create selector from 1 to 9 hours and write the idx here
Domoticz_IDX_max_chargeprice = "1192" # create General, Custom Sensor and write the idx here
Domoticz_IDX_lowest_price = "1195" # create General, Custom Sensor and write the idx here
Domoticz_IDX_current_price = "1196" # create General, Custom Sensor and write the idx here
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
        lowest_price = round(prices_with_time[0][0], 3)
        current_price = round(prices[0],3)
        charge_price_time = datetime.fromisoformat(prices_with_time[int(chargeHours)-1][1]).strftime("%Y-%m-%d %H:%M:%S")
        print("charge_price:", charge_price, "at", charge_price_time)
        print("lowest_price:", lowest_price)
        print("current_price:", current_price)
        # Send the prices to Domoticz
        requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=udevice&idx={Domoticz_IDX_max_chargeprice}&nvalue=0&svalue={charge_price}')
        requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=udevice&idx={Domoticz_IDX_lowest_price}&nvalue=0&svalue={lowest_price}')
        requests.get(f'http://{Domoticz_IP}:{Domoticz_Port}/json.htm?type=command&param=udevice&idx={Domoticz_IDX_current_price}&nvalue=0&svalue={current_price}')
