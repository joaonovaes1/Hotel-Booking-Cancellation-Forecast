import os
import requests

csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hotel_booking_demand.csv')

print(csv_path)  # Para debug


with open(csv_path, 'rb') as f:
     response = requests.post(
        "http://localhost:8000/upload-csv/",
        files={"file": ("hotel_booking_demand.csv", f, "text/csv")},
    )

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
