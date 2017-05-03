from flask import Flask
from datetime import datetime
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello'
    
app.run(port=4000)
