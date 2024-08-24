# Loyalty Points Calculator

This project is a Python Flask application that calculates and updates loyalty points based on customer transactions recorded in Google Sheets. The application fetches transaction data, calculates loyalty points, and updates the Google Sheets accordingly. It also keeps track of the last processed entry to avoid duplicating points.

## Features

- Fetch transaction data from Google Sheets.
- Calculate loyalty points based on the amount paid.
- Update the Google Sheets with calculated loyalty points.
- Track the last processed row to prevent duplication.
- Schedule the loyalty points calculation to run at regular intervals using `APScheduler`.

## Prerequisites

- Python 3.x
- Google Sheets account
- Google API credentials JSON file (for accessing Google Sheets)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/muchokidavid/loyalty-points-calculator.git
    cd loyalty-points-calculator
    ```

2. **Set up a virtual environment (optional but recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up Google API credentials:**

    - Create a Google Cloud project and enable the Google Sheets API.
    - Download the credentials JSON file.
    - Save the JSON file in the project directory and rename it to `creds.json`.

5. **Configure your Google Sheets:**

    - Create two Google Sheets:
      - `Copy of sms loyalty point` - This sheet contains transaction data.
      - `total points` - This sheet will store the total points for each contact.
    - Share both sheets with the email address found in the `creds.json` file.

## Usage

1. **Start the Flask application:**

    ```bash
    python app.py
    ```

2. **Access the application:**

    Open your web browser and go to `http://localhost:5555/`.

3. **Scheduling:**

    The application automatically calculates and updates loyalty points at regular intervals (every minute, as per the scheduler configuration).

## Project Structure

- `app.py`: The main application file containing the Flask server, functions for fetching and updating data, and loyalty points calculations.
- `creds.json`: Google API credentials file (not included in the repo, must be provided).
- `requirements.txt`: A list of Python packages required to run the application.
- `last_processed.txt`: A file to keep track of the last processed row (if using the index tracking method).

## Code Overview

- **Flask Application**: Handles HTTP requests and triggers the loyalty points calculation.
- **Google Sheets Integration**: Uses `gspread` to interact with Google Sheets for reading and updating data.
- **Loyalty Points Calculation**: A function that calculates new loyalty points and updates the sheet.
- **Scheduler**: Uses `APScheduler` to schedule the calculation at regular intervals.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -am 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/) - Web framework used.
- [gspread](https://gspread.readthedocs.io/) - Google Sheets Python API.
- [APScheduler](https://apscheduler.readthedocs.io/) - Advanced Python Scheduler.

