#!/usr/bin/env python3
from flask import Flask, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)
application= app

app.config['SMS_API_KEY'] = os.getenv('SMS_API_KEY') #SMS Api key
app.config['SMS_SENDER_ID'] = os.getenv('SMS_SENDER_ID') #SMS Sender ID
app.config['API_URL'] = os.getenv('API_URL') #SMS SERVER URL
app.config['SMS_USERNAME'] = os.getenv('SMS_USERNAME') #SMS Username
app.config['SMS_PASSWORD'] = os.getenv('SMS_PASSWORD') #SMS Password


scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json",scope)
client = gspread.authorize(creds)

sheet = client.open("Copy of sms loyalty point").sheet1
sheet2 = client.open("total points").sheet1

# Function to get sheet data
def get_data():
    try:
        data = sheet.get_all_records()
        print("Data fetched successfully")
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

# get sheet2 data
def get_sheet_data():
    data = sheet2.get_all_records()
    return data

## Function to find a cell with specific query
def find_cell(query, points):
    try:
        data_num = len(sheet2.get_all_records())
        cell = sheet2.find(str(query))  # find cell with ths data

        if data_num == 0 or cell is None:
            insertRow = [query, points]
            sheet2.insert_row(insertRow, data_num + 2)
            print(f"Added new entry for '{query}' with {points} points.")
            # send message
            send_message(query, 0, points)
        else:
            total_points = get_sheet_data()[cell.row - 2]["TOTAL POINTS"]
            total_points += points
            sheet2.update_cell(cell.row, 2, total_points)  # Update TOTAL POINTS column
            print(f"Found '{query}' at row {cell.row}, column {cell.col}")
            # send message
            send_message(query, total_points - points, total_points)
            return cell

    except StopIteration:
        # If the cell is not found, we handle it here
        print(f"'{query}' not found, adding new entry.")
        insertRow = [query, points]
        sheet2.insert_row(insertRow, data_num + 2)
    except Exception as e:
        print(f"Error finding '{query}': {e}")
        return None


# Function to calculate loyalty points and update the sheet
def calculate_loyalty_points():
    data = get_data()
    if not data:
        return

    updates = []  # Collect cell updates
    for i, row in enumerate(data):
        # Check if this row has been processed
        if row.get("PROCESSED"):
            continue
        
        amount_paid = row["AMOUNT PAID"]
        new_points = amount_paid / 100
        find_cell(row["CONTACT"], new_points)

        updates.append((i + 2, 5, new_points))  # Update LOYALTY POINTS column
        updates.append((i + 2, 6, datetime.now().isoformat()))  # Update "Processed" column with timestamp

    try:
        for row, col, value in updates:
            sheet.update_cell(row, col, value)
        print("Loyalty points updated successfully")
    except Exception as e:
        print(f"Error updating loyalty points: {e}")

# Function to send message (placeholder)
# Function to send message
def send_message(phone, old_points, new_points):
    message = f"You have been successifully been rewarded {new_points - old_points} loyalty points. Your current loyalty point balance is {new_points}."
    payload = {
        'sender_id': app.config['SMS_SENDER_ID'],
        'mobile': phone,
        'msg': message,
        'userid': app.config['SMS_USERNAME'],
        'password': app.config['SMS_PASSWORD'],
        'sendMethod': 'quick',
        'msgType': 'text',
        'output': 'json',
        'duplicatecheck': True
    }
    
    headers = {
        'Authorization': f'Bearer {app.config["SMS_API_KEY"]}', 
        'Content-Type': 'multipart/form-data', 
    }

    response = requests.post(app.config['API_URL'], data=payload, headers=headers)

    if response.status_code == 200:
        print('SMS sent successfully!')
    else:
        print('Failed to send SMS:', response.text)


def get_loyalty_points():
    calculate_loyalty_points()
    print("Loyalty points calculated successfully")
    return jsonify({"message": "Loyalty points calculated successfully"}), 200

# schedule 20 min
# scheduler = BackgroundScheduler()
# scheduler.add_job(func=get_loyalty_points, trigger="interval", minutes=20)
# scheduler.start()

@app.route('/', methods=['GET'])
def hello():
    return get_loyalty_points()
     
if __name__ == '__main__':
    app.run(port=5555, debug=True)
    # app.run()
