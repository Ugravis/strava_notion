SCHEMA = {
  "Name": {"title": {}},
  "Date": {"date": {}},
  "Type": {
    "select": {
      "options": [
        {"name": "Ride"},
        {"name": "Run"}
      ]
    }
  },
  "Distance": {"number": {"format": "number"}},
  "Time (s)": {"number": {"format": "number"}}
}