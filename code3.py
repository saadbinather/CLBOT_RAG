import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import sys
import json
import os
from datetime import datetime
import re

# URL of the Wikipedia page
base_url = "https://en.wikipedia.org/wiki/2025%E2%80%9326_UEFA_Champions_League"

def fetch_page():
    """Fetches the Wikipedia page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return None

def extract_league_table(soup):
    """Specifically extracts the league phase table."""
    print("  📊 Extracting League Table...")
    
    # Find the League Phase section
    league_phase_header = soup.find('span', {'id': 'League_phase'})
    if not league_phase_header:
        league_phase_header = soup.find('span', {'id': 'Table'})
    
    if not league_phase_header:
        return "[League Table section not found on page]"
    
    # Look for the table after this header
    current = league_phase_header.find_parent('h2').find_next_sibling()
    table_content = []
    
    # Try to find the standings table
    found_table = False
    while current and not found_table:
        if current.name == 'table':
            # Check if this is the league table (has Pos, Team, Pld headers)
            table_text = current.get_text()
            if 'Pos' in table_text and 'Team' in table_text and 'Pld' in table_text:
                try:
                    # Parse the table
                    table_html = str(current)
                    df = pd.read_html(StringIO(table_html))[0]
                    
                    # Clean up the dataframe
                    df = df.dropna(how='all')
                    
                    table_content.append("\n🏆 LEAGUE PHASE STANDINGS")
                    table_content.append("-" * 80)
                    
                    # Format each row nicely
                    for _, row in df.iterrows():
                        pos = row.get('Pos', row.get('Position', ''))
                        team = row.get('Team', row.get('Club', ''))
                        pld = row.get('Pld', row.get('MP', ''))
                        w = row.get('W', '')
                        d = row.get('D', '')
                        l = row.get('L', '')
                        gf = row.get('GF', '')
                        ga = row.get('GA', '')
                        gd = row.get('GD', '')
                        pts = row.get('Pts', '')
                        
                        # Clean team name (remove flags and extra formatting)
                        if isinstance(team, str):
                            team = re.sub(r'\[.*?\]', '', team)
                            team = team.strip()
                        
                        line = f"  {pos}. {team:<30} | Pld:{pld} W:{w} D:{d} L:{l} GF:{gf} GA:{ga} GD:{gd} Pts:{pts}"
                        table_content.append(line)
                    
                    found_table = True
                except Exception as e:
                    table_content.append(f"  [Error parsing table: {e}]")
        
        current = current.find_next_sibling()
    
    if not found_table:
        return "[League table data not found in expected format]"
    
    return "\n".join(table_content)

def extract_results(soup):
    """Extracts all match results from the Results section."""
    print("  ⚽ Extracting Results...")
    
    results_header = soup.find('span', {'id': 'Results'})
    if not results_header:
        return "[Results section not found on page]"
    
    current = results_header.find_parent('h2').find_next_sibling()
    results_content = []
    matchday = 0
    
    while current and current.name != 'h2':
        if current.name == 'h3':
            # New matchday
            matchday_text = current.get_text()
            if 'Matchday' in matchday_text:
                matchday += 1
                results_content.append(f"\n📅 MATCHDAY {matchday}")
                results_content.append("-" * 60)
        
        elif current.name == 'table':
            # Match results table
            try:
                table_html = str(current)
                df = pd.read_html(StringIO(table_html))[0]
                
                for _, row in df.iterrows():
                    if len(row) >= 3:
                        home = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                        score = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
                        away = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
                        
                        # Clean up team names
                        home = re.sub(r'\[.*?\]', '', home).strip()
                        away = re.sub(r'\[.*?\]', '', away).strip()
                        
                        if home and score and away and 'Score' not in home:
                            results_content.append(f"  {home:<25} {score:^10} {away:<25}")
            except Exception as e:
                pass
        
        current = current.find_next_sibling()
    
    if not results_content:
        return "[No match results found yet]"
    
    return "\n".join(results_content)

def extract_knockout_phase(soup):
    """Extracts knockout phase information including bracket and results."""
    print("  🏆 Extracting Knockout Phase...")
    
    knockout_header = soup.find('span', {'id': 'Knockout_phase'})
    if not knockout_header:
        return "[Knockout phase section not found]"
    
    current = knockout_header.find_parent('h2').find_next_sibling()
    knockout_content = []
    
    # Extract bracket if present
    bracket_found = False
    while current and current.name != 'h2':
        if current.name == 'div' and 'bracket' in str(current.get('class', '')):
            bracket_found = True
            knockout_content.append("\n🎯 KNOCKOUT BRACKET")
            knockout_content.append("-" * 60)
            
            # Try to extract bracket text
            bracket_text = current.get_text(separator='\n')
            lines = bracket_text.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('v'):
                    knockout_content.append(f"  {line.strip()}")
        
        elif current.name == 'h3':
            round_name = current.get_text()
            knockout_content.append(f"\n{round_name.upper()}")
            knockout_content.append("-" * 40)
        
        elif current.name == 'table':
            try:
                table_html = str(current)
                df = pd.read_html(StringIO(table_html))[0]
                
                for _, row in df.iterrows():
                    if len(row) >= 4:
                        team1 = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                        agg = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
                        team2 = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
                        
                        if 'Team 1' not in team1 and team1 and agg and team2:
                            knockout_content.append(f"  {team1:<25} {agg:^15} {team2:<25}")
            except:
                pass
        
        current = current.find_next_sibling()
    
    if not knockout_content:
        knockout_content.append("[Knockout phase details will be added as the tournament progresses]")
    
    return "\n".join(knockout_content)

def extract_top_scorers(soup):
    """Extracts top scorers information."""
    print("  ⚡ Extracting Top Scorers...")
    
    stats_section = soup.find('span', {'id': 'Top_goalscorers'})
    if not stats_section:
        return "[Top scorers section not found]"
    
    current = stats_section.find_parent('h2').find_next_sibling()
    scorers_content = []
    
    while current and current.name != 'h2':
        if current.name == 'table':
            try:
                table_html = str(current)
                df = pd.read_html(StringIO(table_html))[0]
                
                scorers_content.append("\n⚽ TOP SCORERS")
                scorers_content.append("-" * 60)
                
                for _, row in df.iterrows():
                    rank = row.iloc[0] if len(row) > 0 else ''
                    player = row.iloc[1] if len(row) > 1 else ''
                    team = row.iloc[2] if len(row) > 2 else ''
                    goals = row.iloc[3] if len(row) > 3 else ''
                    minutes = row.iloc[4] if len(row) > 4 else ''
                    
                    if rank and player and 'Rank' not in str(rank):
                        scorers_content.append(f"  {rank}. {player:<25} {team:<25} - {goals} goals ({minutes} min)")
            except:
                pass
        
        current = current.find_next_sibling()
    
    if not scorers_content:
        return "[Top scorers data not available yet]"
    
    return "\n".join(scorers_content)

def extract_qualifying_rounds(soup):
    """Extracts qualifying rounds results."""
    print("  🔄 Extracting Qualifying Rounds...")
    
    qualifying_header = soup.find('span', {'id': 'Qualifying_rounds'})
    if not qualifying_header:
        return "[Qualifying rounds section not found]"
    
    current = qualifying_header.find_parent('h2').find_next_sibling()
    qualifying_content = []
    current_round = ""
    
    while current and current.name != 'h2':
        if current.name == 'h3':
            current_round = current.get_text()
            qualifying_content.append(f"\n{current_round.upper()}")
            qualifying_content.append("-" * 60)
        
        elif current.name == 'table':
            try:
                table_html = str(current)
                df = pd.read_html(StringIO(table_html))[0]
                
                for _, row in df.iterrows():
                    if len(row) >= 4:
                        team1 = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                        agg = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
                        team2 = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
                        first = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ''
                        second = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ''
                        
                        if 'Team 1' not in team1 and team1 and agg and team2:
                            qualifying_content.append(f"  {team1:<25} {agg:^15} {team2:<25}")
                            if first and second:
                                qualifying_content.append(f"    {first:>25} | {second:<25}")
            except:
                pass
        
        current = current.find_next_sibling()
    
    return "\n".join(qualifying_content)

def extract_general_info(soup):
    """Extracts general tournament information."""
    print("  📋 Extracting General Information...")
    
    content = []
    
    # Get intro paragraphs
    intro = soup.find('div', {'class': 'mw-parser-output'})
    if intro:
        for p in intro.find_all('p', recursive=False)[:5]:
            text = p.get_text(strip=True)
            if text and not text.startswith('['):
                content.append(text)
    
    # Get infobox data
    infobox = soup.find('table', class_='infobox')
    if infobox:
        content.append("\n📊 TOURNAMENT OVERVIEW")
        content.append("-" * 40)
        rows = infobox.find_all('tr')
        for row in rows:
            header = row.find('th')
            data = row.find('td')
            if header and data:
                key = header.get_text(strip=True)
                value = data.get_text(strip=True)
                content.append(f"  • {key}: {value}")
    
    return "\n".join(content)

def scrape_complete_data():
    """Main function to scrape all data."""
    print("🔍 SCRAPING UEFA CHAMPIONS LEAGUE 2025-26")
    print("=" * 60)
    
    soup = fetch_page()
    if not soup:
        return None
    
    data = {
        'metadata': {
            'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_url': base_url
        },
        'sections': {}
    }
    
    # Extract each section
    data['sections']['00_General_Information'] = extract_general_info(soup)
    data['sections']['01_Qualifying_Rounds'] = extract_qualifying_rounds(soup)
    data['sections']['02_League_Table'] = extract_league_table(soup)
    data['sections']['03_Results'] = extract_results(soup)
    data['sections']['04_Knockout_Phase'] = extract_knockout_phase(soup)
    data['sections']['05_Top_Scorers'] = extract_top_scorers(soup)
    
    return data

def save_for_rag(data):
    """Saves data in RAG-optimized format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"champions_league_data_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n💾 Saving files to: {output_dir}/")
    
    # 1. Combined file with all sections
    combined_file = os.path.join(output_dir, "00_COMPLETE.txt")
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("UEFA CHAMPIONS LEAGUE 2025-26 - COMPLETE DATA\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {data['metadata']['scrape_date']}\n")
        f.write(f"Source: {data['metadata']['source_url']}\n")
        f.write("=" * 80 + "\n\n")
        
        for section_name, section_content in data['sections'].items():
            f.write(section_content)
            f.write("\n\n" + "=" * 80 + "\n\n")
    
    print(f"  ✅ Combined file: {combined_file}")
    
    # 2. Individual section files
    sections_dir = os.path.join(output_dir, "sections")
    os.makedirs(sections_dir, exist_ok=True)
    
    for section_name, section_content in data['sections'].items():
        # Clean filename
        clean_name = section_name.replace(' ', '_').lower()
        section_file = os.path.join(sections_dir, f"{clean_name}.txt")
        
        with open(section_file, 'w', encoding='utf-8') as f:
            f.write(section_content)
        
        print(f"  ✅ Section: {clean_name}.txt")
    
    # 3. JSON version for structured access
    json_file = os.path.join(output_dir, "data.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ JSON data: {json_file}")
    
    # 4. Create README
    readme_file = os.path.join(output_dir, "README.txt")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("UEFA CHAMPIONS LEAGUE 2025-26 - SCRAPED DATA\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Data scraped: {data['metadata']['scrape_date']}\n\n")
        f.write("SECTIONS:\n")
        for section_name in data['sections'].keys():
            f.write(f"  • {section_name}\n")
        f.write("\nFILES:\n")
        f.write("  • 00_COMPLETE.txt - All sections combined (best for RAG)\n")
        f.write("  • sections/ - Individual section files\n")
        f.write("  • data.json - Structured JSON data\n")
    
    print(f"  ✅ README: {readme_file}")
    
    return output_dir

def print_preview(data):
    """Prints a preview of the scraped data."""
    print("\n" + "=" * 60)
    print("📊 DATA PREVIEW")
    print("=" * 60)
    
    for section_name, content in data['sections'].items():
        preview = content[:200].replace('\n', ' ') + "..." if len(content) > 200 else content
        print(f"\n{section_name}:")
        print(f"  {preview}")

if __name__ == "__main__":
    # Check for required packages
    required = ['requests', 'bs4', 'pandas', 'lxml']
    missing = []
    for package in required:
        try:
            if package == 'bs4':
                import bs4
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing packages. Install with:")
        print(f"pip install {' '.join(missing)}")
        sys.exit(1)
    
    # Scrape the data
    data = scrape_complete_data()
    
    if data:
        # Show preview
        print_preview(data)
        
        # Save files
        output_dir = save_for_rag(data)
        
        print("\n" + "=" * 60)
        print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📁 All files saved to: {output_dir}/")
        print("\n📝 FOR RAG:")
        print("  • Use '00_COMPLETE.txt' for complete context")
        print("  • Individual section files in 'sections/' folder")
    else:
        print("❌ Failed to scrape data.")