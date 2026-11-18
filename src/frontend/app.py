from flask import Flask, render_template, jsonify

app = Flask(__name__)


@app.route("/")
def home():
        track = {
             "song_name": "Come Together",
             "album_name": "Abbey Road"
        }
        
        return render_template("index.html", track=track)


@app.route("/api/status")
def status():
    return jsonify({
        "status": "online",
        "player": "ready"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )