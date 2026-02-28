import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import sys

# URL of the Wikipedia page
url = "https://en.wikipedia.org/wiki/2025%E2%80%9326_UEFA_Champions_League"

def scrape_champions_league_data(url):
    """
    Scrapes the 2025-26 UEFA Champions League Wikipedia page and extracts structured data.
    """
    try:
        # Send a GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}

        # --- 1. Extract Tournament Details from Infobox ---
        infobox = soup.find('table', class_='infobox')
        if infobox:
            tournament_details = {}
            rows = infobox.find_all('tr')
            for row in rows:
                header = row.find('th')
                data_cell = row.find('td')
                if header and data_cell:
                    key = header.get_text(strip=True).replace('\n', ' ')
                    value = data_cell.get_text(strip=True).replace('\n', ' ')
                    tournament_details[key] = value
            data['Tournament Details'] = tournament_details

        # --- 2. Extract Key Statistics ---
        # Look for statistics in the infobox or summary paragraphs
        stats = {}
        # Find the "Tournament statistics" section in infobox
        if infobox:
            stats_header = infobox.find('th', string='Tournament statistics')
            if stats_header:
                parent_row = stats_header.find_parent('tr')
                next_row = parent_row.find_next_sibling('tr')
                if next_row and next_row.find('td'):
                    stats_text = next_row.get_text(separator='|', strip=True)
                    for item in stats_text.split('|'):
                        if ':' in item:
                            key, value = item.split(':', 1)
                            stats[key.strip()] = value.strip()
                        elif '–' in item:
                            # Handle cases like "Matches played 160"
                            parts = item.split()
                            if len(parts) >= 2:
                                key = parts[0]
                                value = ' '.join(parts[1:])
                                stats[key] = value
        data['Tournament Statistics'] = stats

        # --- 3. Extract Association Team Allocation Table ---
        # Find the first table with ranking data (usually has "Rank" header)
        tables = soup.find_all('table', class_='wikitable')
        allocation_tables = []
        for table in tables:
            header_row = table.find('tr')
            if header_row and 'Rank' in header_row.get_text():
                # Convert table to string and wrap in StringIO to avoid FutureWarning
                table_html = str(table)
                df = pd.read_html(StringIO(table_html))[0]
                # Basic cleaning
                df = df.dropna(how='all')
                allocation_tables.append(df)
        
        if allocation_tables:
            data['Association Allocation'] = allocation_tables
        else:
            data['Association Allocation'] = "No allocation table found."

        # --- 4. Extract Distribution and Teams Lists ---
        # Find sections by headings
        distribution_section = soup.find('span', {'id': 'Distribution'})
        if distribution_section:
            # Get the next table after this heading
            next_table = distribution_section.find_next('table', class_='wikitable')
            if next_table:
                table_html = str(next_table)
                distribution_df = pd.read_html(StringIO(table_html))[0]
                data['Distribution'] = distribution_df

        teams_section = soup.find('span', {'id': 'Teams'})
        if teams_section:
            # Get the next table after this heading
            next_table = teams_section.find_next('table', class_='wikitable')
            if next_table:
                table_html = str(next_table)
                teams_df = pd.read_html(StringIO(table_html))[0]
                data['Teams'] = teams_df

        # --- 5. Extract Schedule ---
        schedule_section = soup.find('span', {'id': 'Schedule'})
        if schedule_section:
            # Find the next wikitable after the schedule heading
            next_table = schedule_section.find_next('table', class_='wikitable')
            if next_table:
                table_html = str(next_table)
                schedule_df = pd.read_html(StringIO(table_html))[0]
                data['Schedule'] = schedule_df

        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        return None

def save_to_excel(data, filename="champions_league_2025_26.xlsx"):
    """
    Saves the scraped data to an Excel file with multiple sheets.
    """
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for sheet_name, content in data.items():
                # Clean sheet name (max 31 chars for Excel)
                clean_sheet_name = sheet_name[:31]
                
                if isinstance(content, list):
                    # If there are multiple tables (like association allocation split)
                    for i, df in enumerate(content):
                        if isinstance(df, pd.DataFrame):
                            sheet = f"{clean_sheet_name}_{i+1}"[:31]
                            df.to_excel(writer, sheet_name=sheet, index=False)
                elif isinstance(content, pd.DataFrame):
                    content.to_excel(writer, sheet_name=clean_sheet_name, index=False)
                elif isinstance(content, dict):
                    # Convert dictionary to DataFrame for easy saving
                    df = pd.DataFrame(list(content.items()), columns=['Category', 'Value'])
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
                else:
                    # If it's just text, create a simple DataFrame
                    df = pd.DataFrame({'Data': [content]})
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
        
        print(f"✅ Data successfully saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving to Excel: {e}")
        return False

def print_data(data):
    """
    Prints the scraped data in a readable format.
    """
    for key, value in data.items():
        print(f"\n{'='*60}")
        print(f"📊 {key.upper()}")
        print(f"{'='*60}")
        
        if isinstance(value, pd.DataFrame):
            print(value.to_string(index=False))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                print(f"\n--- Part {i+1} ---")
                if isinstance(item, pd.DataFrame):
                    print(item.to_string(index=False))
                else:
                    print(item)
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(value)

if __name__ == "__main__":
    print("🔍 Scraping data from:", url)
    print("-" * 60)
    
    # Check if required packages are installed
    try:
        import lxml
        print("✅ lxml is installed")
    except ImportError:
        print("❌ lxml is NOT installed. Please install it with: pip install lxml")
        sys.exit(1)
    
    scraped_data = scrape_champions_league_data(url)

    if scraped_data:
        # Print data to console
        print_data(scraped_data)
        
        # Save data to Excel file
        success = save_to_excel(scraped_data)
        if success:
            print("\n✅ Script completed successfully!")
        else:
            print("\n❌ Script completed with errors while saving.")
    else:
        print("❌ Failed to scrape data.")