#!/usr/bin/env python3

from flask import Flask, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json",scope)
client = gspread.authorize(creds)

sheet = client.open("Copy of sms loyalty point").sheet1
sheet2 = client.open("total points").sheet1

# Function to get sheet1 data
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
        cell = sheet2.find(str(query))  # Convert query to string

        if data_num == 0 or cell is None:
            insertRow = [query, points]
            sheet2.insert_row(insertRow, data_num + 2)
            print(f"Added new entry for '{query}' with {points} points.")
        else:
            total_points = get_sheet_data()[cell.row - 2]["TOTAL POINTS"]
            total_points += points
            sheet2.update_cell(cell.row, 2, total_points)  # Update TOTAL POINTS column
            print(f"Found '{query}' at row {cell.row}, column {cell.col}")
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
def send_message(phone, old_points, new_points):
    print(f"Sending message to {phone}: Your loyalty points have been updated from {old_points} to {new_points}.")


def get_loyalty_points():
    calculate_loyalty_points()
    print("Loyalty points calculated successfully")
    return jsonify({"message": "Loyalty points calculated successfully"}), 200

# schedule 20 min
scheduler = BackgroundScheduler()
scheduler.add_job(func=get_loyalty_points, trigger="interval", minutes=20)
scheduler.start()


@app.route('/')
def home():
    return get_loyalty_points()
     
if __name__ == '__main__':
    app.run(port=5555, debug=True)
    # app.run()