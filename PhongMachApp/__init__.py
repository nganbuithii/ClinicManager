import vonage
from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
from vonage import sms

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:%s@localhost/phongmachdb?charset=utf8mb4" % quote('Admin@123')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['PAGE_SIZE'] = 6
app.secret_key = '@##$@#$@#$@%$%$%^%^&%^&%&$%%'



db =SQLAlchemy(app=app)

login = LoginManager(app=app)

cloudinary.config(
    cloud_name="dsbebvfff",
    api_key="825956681133294",
    api_secret="mlg4G6x3cLisjUC_sKx4GiGpYQk"
)
