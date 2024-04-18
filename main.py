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

def weighted_rating(x):
    import pandas as pd
    df2=pd.read_csv(r"Final_Data.csv")
    C= df2['vote_average'].mean()
    m= df2['vote_count'].quantile(0.9)
    v = x['vote_count']
    R = x['vote_average']
    # Calculation based on the IMDB formula
    return (v/(v+m) * R) + (m/(m+v) * C)





def call_homepage(email,cast,crew,genres,check):
    
    if(check==1):
        call_save_details(email,cast,crew,genres)
    
    import pandas as pd 
    import numpy as np 
    df2=pd.read_csv(r"Final_Data.csv")
    q_movies = df2.sort_values('popularity', ascending=False)
    genres=list(genres.split(","))
    cast=list(cast.split(","))
    crew=list(crew.split(","))
    
    genres = [x.strip(' ') for x in genres]
    crew = [x.strip(' ') for x in crew]
    cast = [x.strip(' ') for x in cast]
    
    list_by_genres=pd.DataFrame(columns=['title_x','movie_id'])
    list_by_cast=pd.DataFrame(columns=['title_x','movie_id'])
    list_by_crew=pd.DataFrame(columns=['title_x','movie_id'])

    print(genres,cast,crew)
    for i in range(0,max(len(genres),len(cast),len(crew))):
        try:
            list_by_genres=pd.concat([list_by_genres,q_movies[q_movies['genres'].str.contains(genres[i])][['title_x','movie_id']].head(5)])

        except:
            pass
        try:
            list_by_cast=pd.concat([list_by_cast,q_movies[q_movies['cast'].str.contains(cast[i])][['title_x','movie_id']].head(5)])
        except:
            pass
        try:
            list_by_crew=pd.concat([list_by_crew,q_movies[q_movies['crew'].str.contains(crew[i])][['title_x','movie_id']].head(5)])
        except:
            pass
    list_by_trending=q_movies[['title_x','movie_id']].head(10)
    
    list_by_genres['poster']=[fetch_poster(i) for i in list_by_genres['movie_id']]
    list_by_cast['poster']=[fetch_poster(i) for i in list_by_cast['movie_id']]
    list_by_crew['poster']=[fetch_poster(i) for i in list_by_crew['movie_id']]
    list_by_trending['poster']=[fetch_poster(i) for i in list_by_trending['movie_id']]
    
    b={}
    b.update({"genres":list_by_genres.to_dict("records")})
    b.update({"cast":list_by_cast.to_dict("records")})
    b.update({"crew":list_by_crew.to_dict("records")})
    b.update({"trending":list_by_trending.to_dict("records")})
    
    return b 

def call_save_details(email,cast,crew,genres):
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        # Define the scope of access
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # Authenticate using credentials
        credentials = ServiceAccountCredentials.from_json_keyfile_name(r"cinesense-5b6462fd7feb.json", scope)
        client = gspread.authorize(credentials)
        spreadsheet = client.open("cinesense")
        worksheet = spreadsheet.get_worksheet(1)
        # Find the next available row
        next_row = len(worksheet.col_values(1)) + 1

        # Add data to the next row
        worksheet.update_cell(next_row, 1, email)
        worksheet.update_cell(next_row, 2, cast)
        worksheet.update_cell(next_row, 3, crew)
        worksheet.update_cell(next_row, 4, genres)
        return True

    
def call_home_page_by_mail(a):
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd

    # Define the scope of access
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Authenticate using credentials
    credentials = ServiceAccountCredentials.from_json_keyfile_name(r"cinesense-5b6462fd7feb.json", scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open("cinesense")
    worksheet = spreadsheet.get_worksheet(1)

    all_data = worksheet.get_all_values()

    data=pd.DataFrame(all_data[1:],columns=list(all_data[0]))
    
    b= call_homepage(list(data.email)[0],list(data.cast)[0],list(data.crew)[0],list(data.genres)[0],0)
    return b
    

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

@app.get("/call_homepage")
async def call_homepage_endpoint(email: str, cast: str, crew: str, genres: str, check: int):
    result = call_homepage(email, cast, crew, genres, check)
    if result:
        return result
    else:
        return {"error": "error"}
    return result

@app.get("/call_homepage_by_mail/{email}")
async def call_homepage_by_mail(email: str):
    result = call_home_page_by_mail(email)
    if result:
        return result
    else:
        return {"error": "error"}
    return result
