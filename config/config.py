from dotenv import load_dotenv
import os

load_dotenv(".env")

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
database = os.getenv("MYSQL_DB_NAME") 
port = os.getenv("MYSQL_PORT", "3306")
SECRET_KEY = os.getenv("SECRET_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

DATABASE_CONNECTION_URI = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"