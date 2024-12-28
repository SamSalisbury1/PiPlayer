from flask import Flask, request, redirect
from dotenv import dotenv_values, load_dotenv
import requests
import base64
import urllib.parse

# Spotify API Credentials
load_dotenv(dotenv_path="../.env")
dotenv_variables = dotenv_values("../.env")

PORT = dotenv_variables.get("PORT")
CLIENT_ID = dotenv_variables.get("CLIENT_ID")
CLIENT_SECRET = dotenv_variables.get("CLIENT_SECRET")
REDIRECT_URI = dotenv_variables.get("REDIRECT_URI")
SCOPES = dotenv_variables.get("SCOPES")

app = Flask(__name__)

@app.route("/")
def login():
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://accounts.spotify.com/api/token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        return f"Access Token: {access_token}<br>Refresh Token: {refresh_token}"
    else:
        return f"Error: {response.status_code}, {response.text}"

if __name__ == "__main__":
    app.run(port=PORT)