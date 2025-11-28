import sqlite3
import os
import csv

#declare paths
DATABASE_PATH = "data/database.db"
DE_FULL_PATH = "latest/"

#Create Database
directory = os.path.dirname(DATABASE_PATH)
os.makedirs(directory, exist_ok=True)
open(DATABASE_PATH, "w").close()

con = sqlite3.connect(DATABASE_PATH)
cur = con.cursor()

#initialise Data from txt files

calendar_data = []
with open(DE_FULL_PATH + "calendar.txt", newline="") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=",")
    for row in spamreader:
        calendar_data.append(row)
print("parsed calendar")

trips_data = []
with open(DE_FULL_PATH + "trips.txt", newline="") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=",")
    for row in spamreader:
        trips_data.append(row)
print("parsed trips")
stop_times = []
with open(DE_FULL_PATH + "stop_times.txt", newline="") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=",")
    for row in spamreader:
        stop_times.append(row)
print("parsed stop_times")
#initialize tables
cur.execute("CREATE TABLE service(mon int, tue int, wed int, thur int, fri int, sat int, sun int, start_date int, end_date int, service_id int)")
cur.execute("CREATE TABLE route(route_id int, service_id int, trip_id int)")
cur.execute("CREATE TABLE trip(trip_id int, arrival_time int, departure_time int, stop_id int, stop_sequence int)")
#add data to tables
cur.executemany("INSERT INTO service VALUES (?,?,?,?,?,?,?,?,?,?)", calendar_data[1:])
con.commit()
print("commit 1")
cur.executemany("INSERT INTO route VALUES(?,?,?)", trips_data[1:])
con.commit()
print("commit 2")
cur.executemany("INSERT INTO trip VALUE(?,?,?,?,?)", stop_times[1:])
con.commit()
con.close()