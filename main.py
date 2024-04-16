from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import pickle
import json
import bz2

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

class LoginRequest(BaseModel):
    email: str
    password: str

def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
        data = requests.get(url).json()
        poster_path = data.get('poster_path')
        if poster_path:
            full_path = f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return full_path
        else:
            return None
    except Exception as e:
        return None


def recommended(movie,no):
    movies_list = pickle.load(open(r'df_final.pkl', 'rb'))
    movies = pd.DataFrame(movies_list)
    movies_list = movies['title_x'].values

    ifile = bz2.BZ2File(r"similarity",'rb')
    similarity = pickle.load(ifile)
    index = movies[movies['title_x'] == movie].index[0]
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    lis=[]
    count=0
    for i in distance[1:]:
        if(count>no):
            break
        elif(fetch_poster(movies.loc[i[0]]['movie_id'])==1):
            pass
        else:
            lis.append({
                "name":movies.loc[i[0]]['title_x'],
                "poster":fetch_poster(movies.loc[i[0]]['movie_id'])
            })
            count=count+1
            
    return lis



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
async def login_endpoint(request: LoginRequest):
    email = request.email
    password = request.password
    
    if login(email, password):
        return {"success": True}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

def login(email, password):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        import pandas as pd

        # Define the scope of access
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # Authenticate using credentials
        credentials = ServiceAccountCredentials.from_json_keyfile_name(r"cinesense-5b6462fd7feb.json", scope)
        client = gspread.authorize(credentials)
        sheet = client.open("cinesense").sheet1
        all_data = sheet.get_all_values()

        data=pd.DataFrame(all_data[1:],columns=list(all_data[0]))
        return list(data[data['email']== email]['password'])[0]==password
    except :
        return False

@app.get("/fetch_poster/{movie_id}")
async def fetch_poster_endpoint(movie_id: int):
    poster_url = fetch_poster(movie_id)
    if poster_url:
        return {"poster_url": poster_url}
    else:
        return {"error": "Poster not found"}

@app.get("/movie_detail/{movie_id}")
async def movie_detail_endpoint(movie_id: int):
    try:
        df = pd.read_csv(r'Final_Data.csv')
        movie_data = df[df['movie_id'] == movie_id]
        if not movie_data.empty:
            movie_data['genres'] = movie_data['genres'].str.replace("['", "").str.replace("']", "").str.replace("'", "")
            movie_data['keywords'] = movie_data['keywords'].str.replace("['", "").str.replace("']", "").str.replace("'", "")
            movie_data['cast'] = movie_data['cast'].str.replace("['", "").str.replace("']", "").str.replace("'", "")
            movie_data['crew'] = movie_data['crew'].str.replace("['", "").str.replace("']", "").str.replace("'", "")
            movie_data['poster'] = movie_data['movie_id'].apply(fetch_poster)
            return movie_data.to_dict('records')[0]
        else:
            return {"error": f"No data found for movie ID: {movie_id}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/recommend/{movie}/{no}")
async def recommend_movies(movie: str, no: int):
    recommended_movies = recommended(movie, no)
    if recommended_movies:
        return recommended_movies
    else:
        return {"error": "No recommendations found"}
