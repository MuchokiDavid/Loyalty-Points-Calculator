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
import logging
import time

app = Flask(__name__)
application= app

app.config['SMS_API_KEY'] = os.getenv('SMS_API_KEY') #SMS Api key
app.config['SMS_SENDER_ID'] = os.getenv('SMS_SENDER_ID') #SMS Sender ID
app.config['API_URL'] = os.getenv('API_URL') #SMS SERVER URL
logging.basicConfig(filename='app.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')


scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json",scope)
client = gspread.authorize(creds)

sheet = client.open("sms loyalty point").sheet1
sheet2 = client.open("total points").sheet1

# Function to get sheet1 data
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


def find_cell(name, query, points):
    try:
        data_num = len(sheet2.get_all_records())
        cell = sheet2.find(str(query))  # Find cell with the data

        if data_num == 0 or cell is None:
            insertRow = [name, query, points]
            sheet2.insert_row(insertRow, data_num + 2)
            print(f"Added new entry for '{query}' with {points} points.")
            # Send message
            send_message(query, 0, points, name)
            
            # After inserting, find the newly inserted cell
            cell = sheet2.find(str(query))
            if cell is None:
                logging.error(f"Failed to find the inserted cell for query {query}")
                return None
        else:
            total_points = get_sheet_data()[cell.row - 2]["TOTAL POINTS"]
            total_points += points
            sheet2.update_cell(cell.row, 3, total_points)  # Update TOTAL POINTS column
            print(f"Found '{query}' at row {cell.row}, column {cell.col}")
            # Send message
            send_message(query, total_points - points, total_points, name)
        
        return cell

    except StopIteration:
        # If the cell is not found, handle it here
        print(f"'{query}' not found, adding new entry.")
        insertRow = [name, query, points]
        sheet2.insert_row(insertRow, data_num + 2)
        # Optionally, find the cell again after insertion
        cell = sheet2.find(str(query))
        if cell:
            return cell
        else:
            logging.error(f"Failed to find the inserted cell for query {query}")
            return None
    except Exception as e:
        logging.error(e)
        print(f"Error finding '{query}': {e}")
        return None


# Function to calculate loyalty points and send messages
def calculate_loyalty_points():
    print("Starting loyalty points calculation...")
    
    data = get_data()
    if not data:
        print("No data fetched!")
        return

    print(f"Fetched {len(data)} rows to process.")
    
    for i, row in enumerate(data):
        print(f"Processing row {i+1}: {row}")

        # Skip rows already marked as "PROCESSED"
        if row.get("PROCESSED"):
            print(f"Row {i+1} already processed. Skipping...")
            continue

        amount_paid = row["AMOUNT PAID"]
        new_points = amount_paid / 100  # Adjust point calculation as needed
        print(f"Amount paid: {amount_paid}, calculated points: {new_points}")

        # Find or add cell in the second sheet for the contact
        cell = find_cell(row["NAME"], row["CONTACT"], new_points)
        if cell is None:
            print(f"Error finding or inserting row for {row['CONTACT']}.")
            continue

        # Ensure SMS is sent successfully before marking row as processed
        success = False
        retries = 3
        while not success and retries > 0:
            print(f"Sending SMS to {row['CONTACT']}...")
            success = send_message(row["CONTACT"], 0, new_points, row["NAME"])
            if success:
                print(f"SMS sent successfully to {row['CONTACT']}")
            else:
                print(f"Failed to send SMS to {row['CONTACT']}. Retrying...")
                retries -= 1
                time.sleep(2)

        if not success:
            print(f"Failed to send SMS to {row['CONTACT']} after multiple attempts.")
            continue

        # If successful, update the sheet to mark the row as processed
        try:
            sheet.update_cell(i + 2, 5, new_points)  # Update LOYALTY POINTS column
            sheet.update_cell(i + 2, 6, datetime.now().isoformat())  # Update "Processed" column with timestamp
            print(f"Loyalty points for {row['CONTACT']} updated successfully.")
        except Exception as e:
            logging.error(f"Error updating Google Sheets for {row['CONTACT']}: {e}")
            print(f"Error updating Google Sheets for {row['CONTACT']}: {e}")


def send_message(phone, old_points, new_points, name, retries=3, backoff=2):
    phn = str(phone)
    plus = "+"
    recipient = plus + phn

    message = f"""Dear {name}, You’ve just earned {new_points - old_points} Gas Points! Your new balance is {new_points}. 
    \nOnce you reach 50 points, you will receive special gifts and free giveaways! Thank you for staying loyal to Centorz Gas Points. 
    \nFor any inquiries, feel free to contact us at 0723800950 via call or WhatsApp. """

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


def get_loyalty_points():
    with app.app_context():  # Ensures that the function runs within the app context
        calculate_loyalty_points()
        print("Loyalty points calculated successfully")
        return jsonify({"message": "Loyalty points calculated successfully"}), 200


@app.route('/', methods=['GET'])
def hello():
    # return "<h3>Google sheet</h3>"
    return get_loyalty_points()
    
def main():
    scheduler = BackgroundScheduler()

    # Schedule the job to run every hour
    scheduler.add_job(func=calculate_loyalty_points, trigger='interval', minutes=1)
    scheduler.start()

    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()  # Shut down the scheduler o
     
if __name__ == '__main__':
    main()
    
    
    

# Function to send message
# def send_message(phone, old_points, new_points, name):
#     phn = str(phone)
#     plus= "+"
#     recipient= plus+phn

#     message = f"""Dear {name}, You’ve just earned {new_points - old_points} Gas Points! Your new balance is {new_points}. 
#     Once you reach 50 points, you’ll receive special gifts and free giveaways! Thank you for staying loyal to Centorz Gas Points. 
#     For any inquiries, feel free to contact us at 0723800950 via call or WhatsApp. """
    
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
#         print('Failed to send SMS:', data.get("message"))
#         logging.error(data.get("message"))




# Function to calculate loyalty points and update the sheet
# def calculate_loyalty_points():
#     data = get_data()
#     if not data:
#         return

#     updates = []  # Collect cell updates
#     for i, row in enumerate(data):
#         # Check if this row has been processed
#         if row.get("PROCESSED"):
#             continue
        
#         amount_paid = row["AMOUNT PAID"]
#         new_points = amount_paid / 100
#         find_cell(row["NAME"], row["CONTACT"], new_points)

#         updates.append((i + 2, 5, new_points))  # Update LOYALTY POINTS column
#         updates.append((i + 2, 6, datetime.now().isoformat()))  # Update "Processed" column with timestamp

#     try:
#         for row, col, value in updates:
#             sheet.update_cell(row, col, value)
#         print("Loyalty points updated successfully")
#     except Exception as e:
#         logging.error(e)
#         print(f"Error updating loyalty points: {e}")




# ## Function to find a cell with specific query
# def find_cell(name,query, points):
#     try:
#         data_num = len(sheet2.get_all_records())
#         cell = sheet2.find(str(query))  # find cell with ths data

#         if data_num == 0 or cell is None:
#             insertRow = [name,query, points]
#             sheet2.insert_row(insertRow, data_num + 2)
#             print(f"Added new entry for '{query}' with {points} points.")
#             # send message
#             send_message(query, 0, points,name)
#         # else:
#         total_points = get_sheet_data()[cell.row - 2]["TOTAL POINTS"]
#         total_points += points
#         sheet2.update_cell(cell.row, 3, total_points)  # Update TOTAL POINTS column
#         print(f"Found '{query}' at row {cell.row}, column {cell.col}")
#         # send message
#         send_message(query, total_points - points, total_points,name)
#         return cell

#     except StopIteration:
#         # If the cell is not found, we handle it here
#         print(f"'{query}' not found, adding new entry.")
#         insertRow = [name, query, points]
#         sheet2.insert_row(insertRow, data_num + 2)
#     except Exception as e:
#         logging.error(e)
#         print(f"Error finding '{query}': {e}")
#         return None
