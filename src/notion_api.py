from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime
from rich import print
import os


load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
notion_page_title = "Outdoor tracker"
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
    raise Exception(f"Database {notion_database_title} not found.")

  def add_row(self, data):
    if not self.database_id:
      raise Exception("Database not initialized")
    
    type_emoji = {
        "Run": "👟",
        "Ride": "🚴‍♂️",
        "Swim": "🌊",
        "Hike": "⛰️",
        "Walk": "🚶",
        "Canoeing": "🚣‍♂️"
    }
    emoji = type_emoji.get(data.type, None)
    
    existing_rows = self.client.databases.query(database_id=self.database_id).get("results", [])
    for row in existing_rows:
      row_name = row["properties"]["Name"]["title"][0]["text"]["content"]
      row_date = datetime.fromisoformat(row["properties"]["Date"]["date"]["start"])
      if row_name == data.name and abs((row_date - data.start_date_local).total_seconds()) < 120:
        return
      
    distance_km = data.distance / 1000
    time_min = data.moving_time / 60
    time_h = data.moving_time / 3600

    self.client.pages.create(
      parent={"database_id": self.database_id},
      icon={"type": "emoji", "emoji": emoji},
      properties={
        "Name": {"title": [{"text": {"content": data.name}}]},
        "Type": {"select": {"name": data.type}},
        "Date": {"date": {"start": data.start_date_local.isoformat()}},
        "Km": {"number": round(data.distance / 1000, 2)},
        "Sec": {"number": data.moving_time},
        "D+": {"number": data.total_elevation_gain},
        "Max km / h": {"number": data.max_speed * 3.6},
        "Link": {"url": f"https://www.strava.com/activities/{data.id}"}
      }
    )

    print(f"✨ [white on green]Activity loaded into Notion database[/white on green]: {data.name} ({data.type})")

  def update_medals_by_type(self):
    if not self.database_id:
        raise Exception("Database not initialized")

    # Récupérer toutes les lignes
    rows = self.client.databases.query(database_id=self.database_id, page_size=100)["results"]

    # Les catégories à traiter
    medals = ["🥇", "🥈", "🥉"]  # Préfixe des médailles

    # Grouper les lignes par type
    type_groups = {}
    for row in rows:
        type_name = row["properties"]["Type"]["select"]["name"] if row["properties"]["Type"]["select"] else "Unknown"
        type_groups.setdefault(type_name, []).append(row)

    for type_name, group in type_groups.items():
        # Créer un dictionnaire pour stocker les tags par ligne
        tags_per_row = {row["id"]: [] for row in group}

        # Médailles pour D+ et Km
        for category in ["D+", "Km"]:
            sorted_group = sorted(
                [
                    (row["id"], row["properties"].get(category, {}).get("number"))
                    for row in group
                    if row["properties"].get(category, {}).get("number") is not None
                ],
                key=lambda x: x[1],
                reverse=True  # du plus grand au plus petit
            )
            for i, (row_id, _) in enumerate(sorted_group):
                if i < 3:
                    tags_per_row[row_id].append(f"{medals[i]} {category}")

        # Médailles pour Sec renommé Time (on valorise le plus long)
        sorted_sec = sorted(
            [
                (row["id"], row["properties"].get("Sec", {}).get("number"))
                for row in group
                if row["properties"].get("Sec", {}).get("number") is not None
            ],
            key=lambda x: x[1],
            reverse=True  # du plus long au plus court
        )
        for i, (row_id, _) in enumerate(sorted_sec):
            if i < 3:
                tags_per_row[row_id].append(f"{medals[i]} Tm")

        # Médailles pour Speed = Km / (Sec / 3600)
        sorted_speed = sorted(
            [
                (row["id"], (row["properties"].get("Km", {}).get("number", 0) * 3600) / row["properties"].get("Sec", {}).get("number"))
                for row in group
                if row["properties"].get("Km", {}).get("number") is not None and row["properties"].get("Sec", {}).get("number") not in (None, 0)
            ],
            key=lambda x: x[1],
            reverse=True
        )
        for i, (row_id, _) in enumerate(sorted_speed):
            if i < 3:
                tags_per_row[row_id].append(f"{medals[i]} Spd")

        # Médailles pour Max Speed = Max km / h
        sorted_max_speed = sorted(
            [
                (row["id"], row["properties"].get("Max km / h", {}).get("number", 0))
                for row in group
                if row["properties"].get("Max km / h", {}).get("number") is not None
            ],
            key=lambda x: x[1],
            reverse=True  # du plus rapide au moins rapide
        )
        for i, (row_id, _) in enumerate(sorted_max_speed):
            if i < 3:
                tags_per_row[row_id].append(f"{medals[i]} Mx")

        # Mettre à jour chaque ligne avec tous les tags cumulés
        for row_id, tags in tags_per_row.items():
            self.client.pages.update(
                page_id=row_id,
                properties={
                    "Bests": {
                        "multi_select": [{"name": tag} for tag in tags]
                    }
                }
            )
