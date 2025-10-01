"""
NOTION SCHEMA REFERENCE
"""

SCHEMA = {
  "Name": {"title": {}},
  "Type": {
    "select": {
      "options": [
        {"name": "Ride", "color": "yellow"},
        {"name": "Run", "color": "pink"},
        {"name": "Hike", "color": "green"},
        {"name": "Walk", "color": "gray"},
        {"name": "Canoeing", "color": "blue"}
      ]
    }
  },
  "Date": {"date": {}},
  "Km": {"number": {"format": "number"}},
  "Sec": {"number": {"format": "number"}},
  "D+": {"number": {"format": "number"}},
  "Km / h": {"number": {"format": "number"}},
  "Min / km": {"number": {"format": "number"}},
  "Notes": {"rich_text": {}}
}