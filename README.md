# Consumer Reports Vehicle Reliability Scraper

A tool for scraping vehicle reliability, satisfaction scores, and MPG data from Consumer Reports.

## Requirements

- Python 3.8+
- Consumer Reports subscription
- Required libraries

## Installation

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Install Playwright browsers
playwright install
```

## Configuration

Edit `ConsumerReportsLogins.env` with your credentials:
```
CR_USERNAME=your_username_here
CR_PASSWORD=your_password_here
```

## Usage

### Basic
```bash
python main.py
```
This scrapes data for Toyota, Honda, Mazda, Elantra, Subaru, and Chevrolet vehicles (2010-2025).

### Custom
Modify `main.py`:
```python
# For specific makes:
makes_list = ["Toyota", "Honda"]
vehicles_to_scrape = load_vehicle_data(makes=makes_list)

# For specific years and makes:
vehicles_to_scrape = load_vehicle_data(years=[2020, 2021], makes=["Toyota"])
```

Results are saved to `reliability_scores.csv` with columns:
- make
- model
- year
- reliability_score
- satisfaction_score
- owner_reported_mpg

## Advanced Features

To fetch the latest vehicle data from Consumer Reports, uncomment in `main.py`:
```python
#vehicle_data = scraper.scrape_available_vehicles()
#scraper.save_vehicle_data(vehicle_data)
```

To update vehicle data from NHTSA API:
```bash
python NHTSA_Vehicles_API.py
```

## Example Output

See `ExampleOutput_Toyota_2016_Scores.csv` for reference output format:

```csv
make,model,year,reliability_score,satisfaction_score,owner_reported_mpg
toyota,camry,2016,4,4,32
toyota,corolla,2016,5,3,35
toyota,highlander,2016,5,4,21
...
```

## Author Notes

This code was my attempt at validating how Claude.AI performs in relatively simple scraping tasks. Claude exceeded my expectation. This was all written in under one day. Including the READme!

**Claude's Note:** I enjoyed helping with this project! The combination of Playwright for browser automation and Pandas for data handling creates a robust scraping solution that can adapt to website changes. 
Happy scraping!
