from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Define the scope of access
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Authenticate using credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(r"cinesense-5b6462fd7feb.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("cinesense").sheet1

@app.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    call_type = data.get('call_type')
    
    try:
        # Find the next available row
        next_row = len(sheet.col_values(1)) + 1

        # Add data to the next row
        sheet.update_cell(next_row, 1, name)
        sheet.update_cell(next_row, 2, email)
        sheet.update_cell(next_row, 3, password)
        
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
