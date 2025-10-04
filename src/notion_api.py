from dotenv import load_dotenv
from table_schema import SCHEMA
from notion_client import Client
import os

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
notion_page_title = "Sport"
notion_database_title = "Activities"

class NotionInterface:
  def __init__(self):
    self.client = Client(auth=NOTION_TOKEN)
    self.database_id = None
    self.ensure_database()

  def get_page_id_by_title(self, title: str): 
    response = self.client.search(query=title, filter={"property": "object", "value": "page"})
    for result in response.get("results", []):
      if result.get("object") == "page" and result["properties"].get("title"):
        page_title = result["properties"]["title"]["title"][0]["text"]["content"]
        if page_title == title:
          return result["id"]
    return None
  
  def ensure_database(self):
    page_id = self.get_page_id_by_title(notion_page_title)
    if not page_id:
      raise Exception(f"Page '{notion_page_title}' not found.")

    search_database = self.client.search(query=notion_database_title, filter={"property": "object", "value": "database"})
    for database in search_database.get("results", []):
      if database.get("title", "") == notion_database_title:
        self.database_id = database["id"]
        return
      
    database = self.client.databases.create(
      parent={"type": "page_id", "page_id": page_id},
      title=[{"type": "text", "text": {"content": notion_database_title}}],
      properties=SCHEMA
    )
    self.database_id = database["id"]

  def add_row(self, data):
    if not self.database_id:
      raise Exception("Database not initialized")

    self.client.pages.create(
      parent={"database_id": self.database_id},
      properties={
        "Name": {"title": [{"text": {"content": data.name}}]},
        "Date": {"date": {"start": data.start_date_local.isoformat()}},
        "Type": {"select": {"name": data.type}},
        "Distance": {"number": data.distance},
        "Time (s)": {"number": data.moving_time}
      }
    )
    print(f"Adding {data.name} to Notion database !")