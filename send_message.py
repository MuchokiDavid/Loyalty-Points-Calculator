from flask import Flask, jsonify
from datetime import datetime
import time
from dotenv import load_dotenv
load_dotenv()
import os
import requests

app = Flask(__name__)
application= app

app.config['SMS_API_KEY'] = os.getenv('SMS_API_KEY') #SMS Api key
app.config['SMS_SENDER_ID'] = os.getenv('SMS_SENDER_ID') #SMS Sender ID
app.config['API_URL'] = os.getenv('API_URL') #SMS SERVER URL

# Function to send message
# def send_message(phone, old_points, new_points):
#     phn = str(phone)
#     plus= "+"
#     recipient= plus+phn

#     print(recipient)
#     message = f"You have been successfully rewarded {new_points - old_points} loyalty points. Your new balance is {new_points}."
    
#     payload = {
#         'sender_id': app.config['SMS_SENDER_ID'],
#         'recipient': recipient,
#         'type': 'plain',
#         'message': message
#     }
    
#     headers = {
#         'Authorization': f'Bearer {app.config["SMS_API_KEY"]}', 
#         'Content-Type': 'application/json', 
#         'Accept': 'application/json'
#     }

#     response = requests.post(app.config['API_URL'], json=payload, headers=headers)
#     data=response.json()
#     print(data)

#     if data.get("status") == "success":
#         print('SMS sent successfully!')
#     else:
#         print('Failed to send SMS:', response.text)

def send_message(phone, old_points, new_points, name, retries=3, backoff=2):
    phn = str(phone)
    plus = "+"
    recipient = plus + phn

    message = f"""Dear {name}, You’ve just earned {new_points - old_points} Gas Points! Your new balance is {new_points}. 
    Once you reach 50 points, you’ll receive special gifts and free giveaways! Thank you for staying loyal to Centorz Gas Points. 
    For any inquiries, feel free to contact us at 0723800950 via call or WhatsApp. """

    payload = {
        'sender_id': app.config['SMS_SENDER_ID'],
        'recipient': recipient,
        'type': 'plain',
        'message': message
    }

    headers = {
        'Authorization': f'Bearer {app.config["SMS_API_KEY"]}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    for attempt in range(retries):
        try:
            response = requests.post(app.config['API_URL'], json=payload, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad responses
            data = response.json()
            print(data)

            if data.get("status") == "success":
                print('SMS sent successfully!')
                return True
            else:
                print('Failed to send SMS:', data.get("message"))
                # logging.error(data.get("message"))
                return False
        except Exception as e:
            # logging.error(f"SMS sending failed on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(backoff ** attempt)  # Exponential backoff
            else:
                print('Failed to send SMS after multiple attempts.')
                return False

if __name__ == '__main__':
    send_message(254708697555, 10, 20, "Brian")