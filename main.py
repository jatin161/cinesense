from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()

# Define the scope of access
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Authenticate using credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name("cinesense-5b6462fd7feb.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("cinesense").sheet1

class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str

@app.post("/sign_up")
async def sign_up(request: SignUpRequest):
    name = request.name
    email = request.email
    password = request.password
    call_type = request.call_type
    
    try:
        # Find the next available row
        next_row = len(sheet.col_values(1)) + 1

        # Add data to the next row
        sheet.update_cell(next_row, 1, name)
        sheet.update_cell(next_row, 2, email)
        sheet.update_cell(next_row, 3, password)
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
