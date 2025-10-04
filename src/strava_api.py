from stravaio import strava_oauth2
from stravaio import StravaIO
from notion_api import NotionInterface
from dotenv import load_dotenv
import os

load_dotenv()

token = strava_oauth2(
  client_id = os.getenv("STRAVA_CLIENT_ID"), 
  client_secret = os.getenv("STRAVA_CLIENT_SECRET")
)

client = StravaIO(access_token=token['access_token'])
activities = client.get_logged_in_athlete_activities()
activities = activities[:3] # dev

notion = NotionInterface()

for activity in activities:
  notion.add_row(activity)