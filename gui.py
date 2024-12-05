import customtkinter as tk
import shelve
from main import main

tk.set_appearance_mode("System")
tk.set_default_color_theme("blue")

app = tk.CTk()
app.geometry("400x375")
app.title("StatusCloud")

def clear_shelve(file_path):
    with shelve.open(file_path) as db:
        for key in list(db.keys()):
            del db[key]
        print(f"Shelve file '{file_path}' cleared.")

def pack():
    heading.pack(pady=3)
    airline.pack(pady=3)
    origin.pack(pady=3)
    destination.pack(pady=3)
    flightdate.pack(pady=3)
    dep_time.pack(pady=3)
    arr_time.pack(pady=3)
    submit.pack(pady=3)
    status.pack(pady=3)
    departdelay.pack(pady=3)
    arrivaldelay.pack(pady=3)

heading = tk.CTkLabel(master=app, text="StatusCloud")
airline = tk.CTkEntry(master=app, placeholder_text="Airline", width=300)
origin = tk.CTkEntry(master=app, placeholder_text="Departure Location (Eg. Durango, CO)", width=300)
destination = tk.CTkEntry(master=app, placeholder_text="Arrival Location (Eg. Chicago, IL)", width=300)
flightdate = tk.CTkEntry(master=app, placeholder_text="Date (DD/MM/YYYY)", width=300)
dep_time = tk.CTkEntry(master=app, placeholder_text="Departure Time (HHMM)", width=300)
arr_time = tk.CTkEntry(master=app, placeholder_text="Arrival Time (HHMM)", width=300)
submit = tk.CTkButton(master=app, text="Check Status", command=lambda: send())
status = tk.CTkLabel(master=app, text="Status: ")
departdelay = tk.CTkLabel(master=app, text="Departure Delay: ")
arrivaldelay = tk.CTkLabel(master=app, text="Arrival Delay: ")

def send():
    data = [str(airline.get()), str(origin.get()), str(destination.get()), str(flightdate.get()), str(dep_time.get()), str(arr_time.get())]
    clear_shelve("details")
    
    with shelve.open("details") as outfile:
        outfile["airline"] = data[0]
        outfile["origin"] = data[1]
        outfile["destination"] = data[2]
        outfile["flightdate"] = data[3]
        outfile["dep_time"] = data[4]
        outfile["arr_time"] = data[5]

    flight_status, depdelay, arrdelay = main()

    if flight_status:
        status.configure(text=f"Status: {flight_status}")

    if depdelay is not None:
        departdelay.configure(text=f"Departure delay: {depdelay}")
    if arrdelay is not None:
        arrivaldelay.configure(text=f"Arrival delay: {arrdelay}")

if __name__ == "__main__":
    pack()
    app.mainloop()