import pandas as pd
from dotenv import load_dotenv
from consumer_reports_scraper import ConsumerReportsScraper
from NHTSA_Vehicles_API import load_vehicle_data

# Load environment variables
load_dotenv("ConsumerReportsLogins.env")

def main():

    """
    #### Load vehicle data and get it already formatted for scraping ####
    Example usage:

    vehicles_to_scrape = load_vehicle_data(years=[2020, 2021, 2022], makes=["toyota", "honda"])
    """

    makes_list = ["Toyota", "Honda", "Mazda", "Elantra", "Subaru", "Chevrolet"]
    vehicles_to_scrape = load_vehicle_data(makes=makes_list)

    # Initialize the scraper
    scraper = ConsumerReportsScraper()

    # uncomment this if you need to get available vehicles from Consumer Reports
    #vehicle_data = scraper.scrape_available_vehicles()
    #scraper.save_vehicle_data(vehicle_data)

    try:
        # Scrape all vehicles
        results_df = scraper.scrape_multiple_vehicles(vehicles_to_scrape)
        
        # Save to CSV
        output_file = 'reliability_scores.csv'
        results_df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        # Always close the session when done
        scraper.close_session()

if __name__ == "__main__":
    main()