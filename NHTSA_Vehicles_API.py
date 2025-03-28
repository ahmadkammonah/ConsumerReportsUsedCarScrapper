import json
import requests

def fetch_vehicle_data():
    """Fetch vehicle data from NHTSA API and save to JSON file"""
    # Specific car brands we want to include
    car_brands = [
        "Acura", "Alfa Romeo", "Audi", "BMW", "Bentley", "Buick", "Cadillac", 
        "Chevrolet", "Chrysler", "Dodge", "Fiat", "Fisker", "Ford", "GMC", 
        "Genesis", "Honda", "Hyundai", "Infiniti", "Jaguar", "Jeep", "Kia", 
        "Land Rover", "Lexus", "Lincoln", "Lucid", "Maserati", "Mazda", 
        "Mercedes-Benz", "Mercury", "Mini", "Mitsubishi", "Nissan", "Polestar", 
        "Pontiac", "Porsche", "Ram", "Rivian", "Saab", "Saturn", "Scion", 
        "Scout", "Smart", "Subaru", "Suzuki", "Tesla", "Toyota", "VinFast", 
        "Volkswagen", "Volvo"
    ]
    
    # Get all makes
    makes_url = "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json"
    
    try:
        makes_response = requests.get(makes_url)
        makes_json = makes_response.json()
        
        if "Results" not in makes_json:
            print("API response format is unexpected")
            return {"toyota": ["camry", "corolla"], "honda": ["civic", "accord"]}
            
        # Filter to only include our specified brands (case-insensitive comparison)
        all_makes = makes_json["Results"]
        car_brands_lower = [brand.lower() for brand in car_brands]
        makes_data = [make for make in all_makes if make["Make_Name"].lower() in car_brands_lower]
        
        if not makes_data:
            print("No matching makes found in API response")
            return {"toyota": ["camry", "corolla"], "honda": ["civic", "accord"]}
            
    except Exception as e:
        print(f"Error fetching makes: {e}")
        return {"toyota": ["camry", "corolla"], "honda": ["civic", "accord"]}
    
    vehicle_data = {}
    
    # For each make, get its models
    for make in makes_data:
        make_name = make["Make_Name"].lower()
        vehicle_data[make_name] = []
        
        try:
            # Get models for this make - using Make_ID for more reliable results
            make_id = make["Make_ID"]
            models_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeId/{make_id}?format=json"
            models_response = requests.get(models_url)
            
            # Check if we got the expected structure and handle errors
            models_json = models_response.json()
            if "Results" in models_json and models_json["Results"]:
                models_data = models_json["Results"]
                
                for model in models_data:
                    if "Model_Name" in model:
                        model_name = model["Model_Name"].lower()
                        vehicle_data[make_name].append(model_name)
            else:
                print(f"Could not get models for {make_name} (ID: {make_id})")
                vehicle_data[make_name].append("unknown_model")
        except Exception as e:
            print(f"Error fetching models for {make_name}: {e}")
            vehicle_data[make_name].append("error_model")
    
    # Save to JSON file
    with open("vehicle_data.json", "w") as f:
        json.dump(vehicle_data, f, indent=2)
    
    return vehicle_data

def load_vehicle_data(file_path="vehicle_data.json", years=None, makes=None):
    """Load vehicle data from JSON file and format it for scraping
    
    Args:
        file_path (str): Path to the vehicle data JSON file
        years (list): List of years to include. Defaults to 2010-2025 if None
        makes (list): List of makes to include. Defaults to all makes if None
        
    Returns:
        list: List of dictionaries with make, model, and year ready for scraping
    """
    # Set default years if none provided
    if years is None:
        years = list(range(2010, 2026))  # Years from 2010 to 2025
    
    # Load raw data
    try:
        with open(file_path, "r") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"File {file_path} not found. Fetching data...")
        raw_data = fetch_vehicle_data()
    
    # Filter makes if specified
    if makes is not None:
        # Convert to lowercase for case-insensitive comparison
        makes_lower = [make.lower() for make in makes]
        raw_data = {make: models for make, models in raw_data.items() 
                   if make.lower() in makes_lower}
    
    # Process the data
    vehicles_to_scrape = []
    
    for make, models in raw_data.items():
        # Convert make to lowercase
        make_lower = make.lower()
        
        for model in models:
            # Convert model to lowercase and replace spaces with dashes
            model_formatted = model.lower().replace(' ', '-')
            
            # Add an entry for each year
            for year in years:
                vehicles_to_scrape.append({
                    'make': make_lower,
                    'model': model_formatted,
                    'year': year
                })
    
    return vehicles_to_scrape

if __name__ == "__main__":
    # Run this file to generate the JSON data
    vehicle_data = fetch_vehicle_data()
    print(f"Saved vehicle data for {len(vehicle_data)} makes to vehicle_data.json")