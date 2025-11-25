import kagglehub
import pandas as pd
import os


dataset_path = kagglehub.dataset_download("jessemostipak/hotel-booking-demand")

csv_path = os.path.join(dataset_path, "hotel_bookings.csv")

df = pd.read_csv(csv_path)

df.to_csv("Hotel-Booking-Cancellation-Forecast/data/hotel_booking_demand.csv", index=False)

print("Dataset salvo em Hotel-Booking-Cancellation-Forecast/data/hotel_booking_demand.csv")
print(df.head())
