from flask import Flask
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
load_dotenv()
app=Flask(__name__)
@app.route("/")
def hello():
    return 'Hello world'


if __name__=="__main__":
    app.run(debug=True)