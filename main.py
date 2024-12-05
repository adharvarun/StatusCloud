import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import KNNImputer
import numpy as np
import shelve

def load_and_preprocess_data(file_path, top_n=500):
    try:
        df = pd.read_csv(file_path, dtype={'DepTime': str, 'ArrTime': str, 'OriginCityName': str, 'DestCityName': str, 'FlightDate': str}, low_memory=False)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    
    df_new = df.groupby("Airline").head(top_n).copy()

    df_new["Airline"] = df_new["Airline"].str.lower()
    df_new["OriginCityName"] = df_new["OriginCityName"].str.lower()
    df_new["DestCityName"] = df_new["DestCityName"].str.lower()
    df_new["FlightDate"] = pd.to_datetime(df_new["FlightDate"], format='%d/%m/%Y')

    return df_new

def extend_label_encoder(le, new_labels):
    # Extend existing label encoder with new labels
    le_classes = le.classes_.tolist()
    for label in new_labels:
        if label not in le_classes:
            le_classes.append(label)
    le.classes_ = np.array(le_classes)

def encode_features(df, encoders=None):
    if encoders is None:
        encoders = {
            "Airline": LabelEncoder(),
            "OriginCityName": LabelEncoder(),
            "DestCityName": LabelEncoder()
        }
        for feature in encoders:
            df[feature] = encoders[feature].fit_transform(df[feature])
    else:
        for feature in encoders:
            extend_label_encoder(encoders[feature], df[feature].unique())
            df[feature] = encoders[feature].transform(df[feature])

    df['FlightDate'] = df['FlightDate'].astype(np.int64) // 10**9

    return df, encoders

def find_flight(df, airline, date, origin, destination, dep_time, arr_time):
    date = pd.to_datetime(date, format='%d/%m/%Y').to_numpy().astype('int64') // 10**9
    matching_rows = df[
        (df["Airline"] == airline.lower()) &
        (df["FlightDate"] == date) &
        (df["OriginCityName"] == origin.lower()) &
        (df["DestCityName"] == destination.lower()) &
        (df["DepTime"] == str(dep_time)) &
        (df["ArrTime"] == str(arr_time))
    ]

    if not matching_rows.empty:
        return matching_rows
    else:
        return None

def find_similar_flights(df, airline, date, origin, destination, dep_time, arr_time, k=5):
    features = ['Airline', 'FlightDate', 'OriginCityName', 'DestCityName', 'DepTime', 'ArrTime']
    X = df[features].copy()

    X, encoders = encode_features(X)

    imputer = KNNImputer(n_neighbors=5)
    X_imputed = imputer.fit_transform(X)

    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_imputed, X.index)

    query_date = pd.to_datetime(date, format='%d/%m/%Y').to_numpy().astype('int64') // 10**9
    
    # Handle unseen labels
    extend_label_encoder(encoders['Airline'], [airline.lower()])
    extend_label_encoder(encoders['OriginCityName'], [origin.lower()])
    extend_label_encoder(encoders['DestCityName'], [destination.lower()])

    query_point = pd.DataFrame({
        'Airline': [encoders['Airline'].transform([airline.lower()])[0]],
        'FlightDate': [query_date],
        'OriginCityName': [encoders['OriginCityName'].transform([origin.lower()])[0]],
        'DestCityName': [encoders['DestCityName'].transform([destination.lower()])[0]],
        'DepTime': [str(dep_time)],
        'ArrTime': [str(arr_time)]
    })

    query_point_imputed = imputer.transform(query_point)

    similar_flight_indices = knn.kneighbors(query_point_imputed, return_distance=False)[0]

    return df.iloc[similar_flight_indices]

def main():
    file_path = "data.csv"
    df = load_and_preprocess_data(file_path)

    if df is None:
        return
    
    infile = shelve.open("details")
    airline = infile["airline"]
    date = infile["flightdate"]
    origin = infile["origin"]
    destination = infile["destination"]
    dep_time = infile["dep_time"]
    arr_time = infile["arr_time"]

    print(airline, date, origin, destination, dep_time, arr_time)
    
    flight = find_flight(df, airline, date, origin, destination, dep_time, arr_time)

    if flight is not None:
        print("Found matching flight:")
        print(flight)
        return flight
    else:
        print("No exact match found. Finding similar flights...")
        similar_flights = find_similar_flights(df, airline, date, origin, destination, dep_time, arr_time)
        print("Similar flights:")
        print(similar_flights)
        similar_flight = similar_flights.iloc[0]
        status = "On Time"

        if similar_flight["Cancelled"] == "TRUE":
            status = "Cancelled"
        
        if similar_flight["Diverted"] == "TRUE":
            status = "Diverted"

        depdelay = similar_flight["DepDelayMinutes"]
        arrdelay = similar_flight["ArrDelayMinutes"]

        return status, depdelay, arrdelay

if __name__ == "__main__":
    main()
