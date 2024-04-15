from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

app = FastAPI()

# Define the scope of access
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Authenticate using credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(r"cinesense-5b6462fd7feb.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("cinesense").sheet1
all_data = sheet.get_all_values()

data = pd.DataFrame(all_data[1:], columns=list(all_data[0]))

# Define CORS origins
origins = [
    "https://cine-sense.netlify.app",  # Adjust this to match your Netlify app's origin
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}

@app.head("/")
async def head_root():
    return

@app.post("/sign_up")
async def sign_up(request: SignUpRequest):
    name = request.name
    email = request.email
    password = request.password
    
    try:
        # Find the next available row
        next_row = len(sheet.col_values(1)) + 1

        # Add data to the next row
        sheet.update_cell(next_row, 1, name)
        sheet.update_cell(next_row, 2, email)
        sheet.update_cell(next_row, 3, password)
        
        # Add the 'Access-Control-Allow-Origin' header
        response_headers = {
            "Access-Control-Allow-Origin": "https://cine-sense.netlify.app",
            "Access-Control-Allow-Credentials": "true",
        }
        
        return {"success": True}, response_headers
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/login")
async def login(email: str, password: str):
    try:
        return list(data[data['email']== email]['password'])[0]==password
    except :
        return False
