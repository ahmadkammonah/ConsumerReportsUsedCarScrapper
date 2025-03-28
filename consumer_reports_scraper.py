import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import pandas as pd
import time

class ConsumerReportsScraper:
    def __init__(self):
        self.username = os.getenv('CR_USERNAME')
        self.password = os.getenv('CR_PASSWORD')
        self.playwright = None
        self.browser = None
        self.page = None
        
    def start_session(self):
        """Initialize the browser session and login"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        
        try:
            # Navigate to main page
            self.page.goto('https://www.consumerreports.org/')
            
            # Click Sign In button
            self.page.click('span.cda-gnav__main-sign-in')
            
            # Wait for login fields
            self.page.wait_for_selector('#gnav-signin-username')
            
            # Input credentials
            self.page.locator('#gnav-signin-username').fill(str(self.username))
            self.page.wait_for_timeout(500)
            self.page.locator('#gnav-signin-password').fill(str(self.password))
            
            # Submit login
            self.page.click('#gnav-signin-submit')
            
            # Wait for login
            self.page.wait_for_load_state('networkidle', timeout=10000)
            print("Successfully logged in")
            return True
            
        except Exception as e:
            print(f"Error during login: {e}")
            self.close_session()
            return False
    
    def scrape_vehicle(self, make, model, year, vehicle_data=None):
        """Scrape data for a specific vehicle from the overview page
        
        Args:
            make (str): Vehicle make (manufacturer)
            model (str): Vehicle model
            year (int): Vehicle year
            vehicle_data (dict, optional): Pre-loaded vehicle data to validate year availability
            
        Returns:
            dict: Scraped vehicle data or None if unavailable/invalid
        """
        if not self.page:
            print("No active session. Call start_session() first.")
            return None
            
        # Check if year is available for this make/model if vehicle_data is provided
        if vehicle_data:
            try:
                if make in vehicle_data and model in vehicle_data[make]:
                    available_years = vehicle_data[make][model]
                    # Ensure year is an integer for comparison
                    year_int = int(year) if not isinstance(year, int) else year
                    if year_int not in available_years:
                        print(f"Skipping {make} {model} {year} - Year not available in Consumer Reports")
                        #print(f"Available years: {available_years}")
                        return None
                else:
                    # Check for case-insensitive matches
                    found_make = False
                    found_model = False
                    
                    for data_make in vehicle_data.keys():
                        if data_make.lower() == make.lower():
                            found_make = True
                            make_key = data_make
                            
                            for data_model in vehicle_data[data_make].keys():
                                if data_model.lower() == model.lower():
                                    found_model = True
                                    model_key = data_model
                                    
                                    # Found matching make/model with different case
                                    available_years = vehicle_data[make_key][model_key]
                                    year_int = int(year) if not isinstance(year, int) else year
                                    if year_int in available_years:
                                        print(f"Found case-insensitive match: {make_key} {model_key} {year}")
                                        # Update make/model to match the case in the data
                                        make = make_key
                                        model = model_key
                                        break
                                    else:
                                        print(f"Skipping {make} {model} {year} - Year not available in Consumer Reports")
                                        #print(f"Available years: {available_years}")
                                        return None
                            
                            if not found_model:
                                print(f"Skipping {make} {model} {year} - Model not available in Consumer Reports")
                                #print(f"Available models for {make_key}: {list(vehicle_data[make_key].keys())}")
                                return None
                            break
                    
                    if not found_make:
                        print(f"Skipping {make} {model} {year} - Make not available in Consumer Reports")
                        #print(f"Available makes: {list(vehicle_data.keys())}")
                        return None
            except Exception as e:
                print(f"Error checking vehicle availability: {e}")
                print(f"Will attempt to scrape {make} {model} {year} anyway")
                # Continue with scraping attempt if data validation fails
        
        try:
            # Navigate to car overview page
            url = f'https://www.consumerreports.org/cars/{make.lower()}/{model.lower()}/{year}/overview'
            self.page.goto(url)
            
            # Wait for page to load
            self.page.wait_for_load_state('networkidle')
            
            # Find all score elements
            score_elements = self.page.query_selector_all('span.crux-body-copy.crux-body-copy--extra-small--bold.bar-ratings-chart__score')
            
            reliability_score = 'N/A'
            satisfaction_score = 'N/A'
            
            # Try to find reliability and satisfaction scores
            for i, element in enumerate(score_elements):
                text = element.inner_text().strip()
                # Use position to determine which score we're looking at
                if i == 0:  # First score is usually reliability
                    reliability_score = text
                elif i == 1:  # Second score is usually satisfaction
                    satisfaction_score = text
            
            # Find owner reported MPG and extract just the number
            mpg_element = self.page.query_selector('div.fuel-efficiency-component__text-box.qa-qwner-reported-mpg b')
            if mpg_element:
                mpg_text = mpg_element.inner_text().strip()
                # Extract just the number from text like "26 MPG"
                import re
                mpg_match = re.search(r'(\d+)', mpg_text)
                owner_reported_mpg = mpg_match.group(1) if mpg_match else mpg_text
            else:
                owner_reported_mpg = 'N/A'
            
            result = {
                'make': make,
                'model': model,
                'year': year,
                'reliability_score': reliability_score,
                'satisfaction_score': satisfaction_score,
                'owner_reported_mpg': owner_reported_mpg
            }
            
            print(f"Scraped: {make} {model} {year} - Reliability: {reliability_score}, Satisfaction: {satisfaction_score}, MPG: {owner_reported_mpg}")
            return result
        
        except Exception as e:
            print(f"Error scraping {make} {model} {year}: {e}")
            return None
    
    def scrape_multiple_vehicles(self, vehicles_list):
        """Scrape multiple vehicles and return results as a DataFrame
        
        Args:
            vehicles_list: List of dicts with keys 'make', 'model', 'year'
        
        Returns:
            pandas.DataFrame with results
        """
        if not self.start_session():
            return pd.DataFrame()
            
        results = []
        
        # Load vehicle data for validation
        vehicle_data = self.load_vehicle_data()
        if not vehicle_data:
            print("Warning: Could not load vehicle data for validation. Will attempt to scrape all vehicles.")
        
        for vehicle in vehicles_list:
            result = self.scrape_vehicle(
                vehicle['make'], 
                vehicle['model'], 
                vehicle['year'],
                vehicle_data
            )
            
            if result:
                results.append(result)
            
            # Optional: Add a small delay between requests
            time.sleep(1)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        return df
    
    def scrape_available_vehicles(self):
        """Scrape all available makes, models, and years from Consumer Reports
        
        Returns:
            dict: Nested dictionary with structure {make: {model: [years]}}
        """
        if not self.page:
            if not self.start_session():
                return {}
                
        print("Starting to scrape available vehicles...")
        result = {}
        
        try:
            # Navigate to cars page
            self.page.goto('https://www.consumerreports.org/cars/')
            self.page.wait_for_load_state('networkidle')
            
            # Click on Select Make button - using the selector class instead of text
            make_selector = self.page.query_selector('.cr-selector__title button.cr-selector__value')
            if make_selector:
                make_selector.click()
            self.page.wait_for_selector('.cr-cf-chunked-options__item')
            
            # Get all available makes
            make_elements = self.page.query_selector_all('.cr-cf-chunked-options__item')
            makes = [element.inner_text().strip() for element in make_elements]
            print(f"Found {len(makes)} makes")
            print (makes)


            self.page.click('h1')
            # Iterate through each make
            for make in makes:
                print(f"Processing make: {make}")
                result[make] = {}
                
                # Click on Select Make button - using selector class instead of text
                make_selector = self.page.query_selector('.cr-selector__title button.cr-selector__value')
                if make_selector:
                    make_selector.click()
                self.page.wait_for_selector('.cr-cf-chunked-options__item')
                
                # Click on the specific make - more precise selector
                try:
                    self.page.click(f'.cr-cf-chunked-options__item span.crux-body-copy:text-is("{make}")')
                except Exception:
                    # Try alternative approach using JavaScript if the click fails
                    self.page.evaluate(f'''
                        Array.from(document.querySelectorAll('.cr-cf-chunked-options__item span.crux-body-copy'))
                            .find(el => el.textContent.trim() === "{make}")?.closest('.cr-cf-chunked-options__item')?.click();
                    ''')
                self.page.wait_for_timeout(1000)  # Add small delay after click
                #self.page.click('h1')
                # Click on Select Model button
                try:
                    #self.page.wait_for_selector('button.cr-selector__value:has-text("Select Model ")', timeout=5000)
                    #self.page.click('button.cr-selector__value:has-text("Select Model ")')
                    #self.page.wait_for_selector('.cr-cf-chunked-options__item')
                    
                    # Get all available models for this make using a more specific selector
                    # Target the model options container specifically to avoid getting makes again
                    model_elements = self.page.query_selector_all('.cr-cf-model-options .cr-cf-chunked-options__item')
                    models = [element.inner_text().strip() for element in model_elements]
                    print(f"  Found {len(models)} models for {make}")
                    print (models)

                    # Iterate through each model
                    for model in models:
                        print(f"  Processing model: {model}")
                        
                        # Click on Select Model button using selector classes
                        #model_selector = self.page.query_selector_all('.cr-selector__title button.cr-selector__value')[1]
                        #if model_selector:
                        #    model_selector.click()
                        #self.page.wait_for_selector('.cr-cf-chunked-options__item')
                        
                        # Click on the specific model - more precise selector
                        try:
                            # First approach: Try to find and click the model element using a basic selector
                            model_selector = f'.cr-cf-model-options .cr-cf-chunked-options__item:has-text("{model}")'
                            if self.page.query_selector(model_selector):
                                self.page.click(model_selector)
                            else:
                                # Second approach: Use JavaScript for more flexible text matching
                                self.page.evaluate(f'''
                                    Array.from(document.querySelectorAll('.cr-cf-model-options .cr-cf-chunked-options__item'))
                                        .find(el => el.textContent.trim() === "{model}")?.click();
                                ''')
                        except Exception as e:
                            print(f"    Error clicking model {model}: {e}")
                            # Third approach: Direct JavaScript DOM traversal and click
                            try:
                                self.page.evaluate(f'''
                                    (function() {{
                                        const modelItems = document.querySelectorAll('.cr-cf-model-options .cr-cf-chunked-options__item');
                                        for (let item of modelItems) {{
                                            const text = item.textContent.trim();
                                            if (text === "{model}") {{
                                                item.click();
                                                return true;
                                            }}
                                        }}
                                        return false;
                                    }})();
                                ''')
                            except Exception as e2:
                                print(f"    All attempts to click model {model} failed: {e2}")
                        
                        self.page.wait_for_timeout(1000)  # Add small delay after click
                        
                        # Click on Year button
                        try:
                            # Click on Year button using selector classes
                            #year_selector = self.page.query_selector_all('.cr-selector__title button.cr-selector__value')[2]
                            #if year_selector:
                            #    year_selector.click()
                            #self.page.wait_for_selector('.cr-cf-grouped-options__item')
                            
                            # Get all available years for this model
                            year_elements = self.page.query_selector_all('.cr-cf-grouped-options__item')
                            years = [int(element.inner_text().strip()) for element in year_elements]
                            print(f"    Found {len(years)} years for {make} {model}")
                            
                            result[make][model] = years
                            
                            # Close the year dropdown by clicking outside
                            self.page.click('h1')
                        except Exception as e:
                            print(f"    Error getting years for {make} {model}: {e}")
                            result[make][model] = []

                        # Use position-based selector for the model dropdown (second dropdown)
                        # Wait for the selector to be available
                        self.page.wait_for_selector('.cr-selector__title button.cr-selector__value', timeout=5000)
                        
                        # Get all selector buttons and click the second one (model selector)
                        selector_buttons = self.page.query_selector_all('.cr-selector__title button.cr-selector__value')
                        if len(selector_buttons) >= 2:
                            # Click the model selector (second dropdown)
                            selector_buttons[1].click()
                        else:
                            # If we can't find it by position, try JavaScript approach
                            self.page.evaluate('''
                                document.querySelectorAll('.cr-selector__title button.cr-selector__value')[1].click();
                            ''')
                            
                        self.page.wait_for_selector('.cr-cf-chunked-options__item')
                except Exception as e:
                    print(f"  Error getting models for {make}: {e}")
            
            return result
            
        except Exception as e:
            print(f"Error scraping available vehicles: {e}")
            return result
            
    def save_vehicle_data(self, data, filename='vehicle_data.json'):
        """Save vehicle data to a JSON file
        
        Args:
            data (dict): Vehicle data to save
            filename (str): Path to output file
        """
        import json
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Vehicle data saved to {filename}")
            
    def load_vehicle_data(self, filename='vehicle_data.json'):
        """Load vehicle data from a JSON file
        
        Args:
            filename (str): Path to input file
            
        Returns:
            dict: Vehicle data
        """
        import json
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading vehicle data: {e}")
            return {}
    
    def close_session(self):
        """Close the browser session"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = None
        self.playwright = None
        self.page = None
        print("Session closed")