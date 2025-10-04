from dotenv import load_dotenv
from table_schema import SCHEMA
from notion_client import Client
from datetime import datetime
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

    children = self.client.blocks.children.list(page_id)["results"]
    for child in children:
      if child["type"] == "child_database" and child["child_database"]["title"] == notion_database_title:
        self.database_id = child["id"]
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
    
    existing_rows = self.client.databases.query(database_id=self.database_id).get("results", [])
    for row in existing_rows:
      row_name = row["properties"]["Name"]["title"][0]["text"]["content"]
      row_date = datetime.fromisoformat(row["properties"]["Date"]["date"]["start"])
      print('######')
      print(row_date)
      print(data.start_date_local)
      print('------')
      print(row_name)
      print(data.name)
      print('######')
      if row_name == data.name and abs((row_date - data.start_date_local).total_seconds()) < 120:
        print('skip')
        return

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