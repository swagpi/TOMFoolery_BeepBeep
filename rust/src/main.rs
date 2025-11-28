use chrono;
use csv::Reader;
use rusqlite::{Connection, Transaction};
use serde::Deserialize;
use std::{error::Error, fs};

// Input files
const CALENDAR: &str = "data/calendar.txt";
const TRIPS: &str = "data/trips.txt";
const STOP_TIMES: &str = "data/stop_times.txt";
const STOPS: &str = "data/stops.txt";

// -------------------------
// Data structures
// -------------------------
#[derive(Debug, Deserialize)]
struct Service {
    #[serde(rename = "monday")]
    mon: u8,
    #[serde(rename = "tuesday")]
    tue: u8,
    #[serde(rename = "wednesday")]
    wed: u8,
    #[serde(rename = "thursday")]
    thu: u8,
    #[serde(rename = "friday")]
    fri: u8,
    #[serde(rename = "saturday")]
    sat: u8,
    #[serde(rename = "sunday")]
    sun: u8,
    start_date: i32,
    end_date: i32,
    service_id: i32,
}

#[derive(Deserialize, Debug)]
struct Trip {
    route_id: i32,
    service_id: i32,
    trip_id: i32,
}

#[derive(Deserialize, Debug)]
struct StopTime {
    trip_id: i32,
    arrival_time: chrono::NaiveTime,
    departure_time: chrono::NaiveTime,
    stop_id: i32,
    stop_sequence: i32,
}

#[derive(Deserialize, Debug)]
struct Stop {
    stop_id: i32,
    stop_name: String,
    stop_lat: f64,
    stop_lon: f64,
    #[serde(default)]
    location_type: Option<i32>,
}

// -------------------------
// Table creation
// -------------------------
fn create_tables(db: &Connection) {
    db.execute(
        "CREATE TABLE IF NOT EXISTS service(
            mon int, tue int, wed int, thur int, fri int,
            sat int, sun int, start_date int, end_date int, service_id int
        )", ()
    ).unwrap();

    db.execute(
        "CREATE TABLE IF NOT EXISTS trip(
            route_id int, service_id int, trip_id int
        )",
        (),
    ).unwrap();

    db.execute(
        "CREATE TABLE IF NOT EXISTS stoptime(
            trip_id int,
            arrival_time text,
            departure_time text,
            stop_id int,
            stop_sequence int
        )", ()
    ).unwrap();

    db.execute(
        "CREATE TABLE IF NOT EXISTS stops(
            stop_name text,
            longitude real,
            latitude real,
            stop_id int,
            location_type int
        )", ()
    ).unwrap();
}

// -------------------------
// Loaders
// -------------------------
fn load_service(tx: &Transaction) -> Result<(), Box<dyn Error>> {
    let mut stmt = tx.prepare(
        "INSERT INTO service VALUES(?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)"
    )?;

    let file = fs::File::open(CALENDAR)?;
    let mut reader = Reader::from_reader(file);

    for result in reader.deserialize() {
        let s: Service = result?;
        stmt.execute((
            s.mon, s.tue, s.wed, s.thu, s.fri, s.sat, s.sun,
            s.start_date, s.end_date, s.service_id,
        ))?;
    }
    Ok(())
}

fn load_trips(tx: &Transaction) -> Result<(), Box<dyn Error>> {
    let mut stmt = tx.prepare("INSERT INTO trip VALUES(?1, ?2, ?3)")?;
    let file = fs::File::open(TRIPS)?;
    let mut reader = Reader::from_reader(file);

    for result in reader.deserialize() {
        let t: Trip = result?;
        stmt.execute((t.route_id, t.service_id, t.trip_id))?;
    }
    Ok(())
}

fn load_stoptimes(tx: &Transaction) -> Result<(), Box<dyn Error>> {
    let mut stmt = tx.prepare(
        "INSERT INTO stoptime VALUES(?1, ?2, ?3, ?4, ?5)"
    )?;

    let file = fs::File::open(STOP_TIMES)?;
    let mut reader = Reader::from_reader(file);

    for result in reader.deserialize() {
        let st: StopTime = result?;
        stmt.execute((
            st.trip_id,
            st.arrival_time.format("%H%M%S").to_string(),
            st.departure_time.format("%H%M%S").to_string(),
            st.stop_id,
            st.stop_sequence,
        ))?;
    }
    Ok(())
}

fn load_stops(tx: &Transaction) -> Result<(), Box<dyn Error>> {
    let mut stmt = tx.prepare(
        "INSERT INTO stops(stop_name, longitude, latitude, stop_id, location_type)
         VALUES (?1, ?2, ?3, ?4, ?5)"
    )?;

    let file = fs::File::open(STOPS)?;
    let mut reader = Reader::from_reader(file);

    for result in reader.deserialize() {
        let s: Stop = result?;
        stmt.execute((
            s.stop_name,
            s.stop_lon,
            s.stop_lat,
            s.stop_id,
            s.location_type.unwrap_or(0),
        ))?;
    }
    Ok(())
}

// -------------------------
// Main
// -------------------------
fn main() {
    const DB_FILE: &str = "database.db";
    let mut base_path = std::env::var("DB_DIR").unwrap().to_string();
    base_path.push_str(DB_FILE);

    let mut db = Connection::open(&base_path).unwrap();

    create_tables(&db);

    let tx = db.transaction().unwrap();
    load_service(&tx).unwrap();
    load_trips(&tx).unwrap();
    load_stoptimes(&tx).unwrap();
    load_stops(&tx).unwrap();
    tx.commit().unwrap();

    println!("Database created successfully.");
}
