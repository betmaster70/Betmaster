
import streamlit as st
import requests
from datetime import datetime
from fpdf import FPDF

API_KEY = '1f0e3a6f6e8437ada8118c3ac27bb2e5'
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {'x-apisports-key': API_KEY}

MAJOR_LEAGUE_IDS = [39, 140, 135, 78, 61]  # EPL, La Liga, Serie A, Bundesliga, Ligue 1

def get_all_fixtures_today():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={today}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get('response', [])

def get_odds_for_fixture(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    if response.status_code != 200 or not data['response']:
        return None

    try:
        for bookmaker in data['response'][0]['bookmakers']:
            if bookmaker['name'] in ['1xBet', 'Bet365']:
                for bet in bookmaker['bets']:
                    if bet['name'] == 'Match Winner':
                        odds = bet['values']
                        return {
                            'home': float(odds[0]['odd']),
                            'draw': float(odds[1]['odd']),
                            'away': float(odds[2]['odd'])
                        }
    except:
        pass
    return None

def calculate_ev(odd):
    if odd == 0:
        return -100
    return round(((1 / odd) * 100) - 100, 2)

def generate_pdf(bets):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="BetMaster - Top Value Bets", ln=True, align="C")
    pdf.ln(10)

    for bet in bets:
        line = f"{bet['Match']} ({bet['League']}) - {bet['Outcome']} @ {bet['Odd']} (EV: {bet['EV (%)']}%)"
        pdf.multi_cell(0, 10, line)

    pdf_path = "/tmp/betmaster_value_bets.pdf"
    pdf.output(pdf_path)
    return pdf_path

st.set_page_config(page_title="BetMaster", layout="wide")
st.title("🎯 BetMaster")
st.caption("Powered by Zedd the Master. Real OG of code.")

extra_league_id = st.text_input("➕ Add another League ID (optional):", "")
if extra_league_id:
    try:
        extra_league_id = int(extra_league_id)
        MAJOR_LEAGUE_IDS.append(extra_league_id)
    except:
        st.warning("Invalid league ID. Please enter a number.")

if st.button("🔍 Scan Today’s Matches"):
    st.info("Scanning matches for value bets...")
    fixtures = get_all_fixtures_today()
    value_bets = []

    for match in fixtures:
        league_id = match['league']['id']
        if league_id not in MAJOR_LEAGUE_IDS:
            continue

        fixture_id = match['fixture']['id']
        home = match['teams']['home']['name']
        away = match['teams']['away']['name']
        time = match['fixture']['date'][11:16]
        league = match['league']['name']

        odds = get_odds_for_fixture(fixture_id)
        if not odds:
            continue

        for outcome in ['home', 'draw', 'away']:
            odd = odds[outcome]
            ev = calculate_ev(odd)
            if ev > 0:
                value_bets.append({
                    'Match': f"{home} vs {away} @ {time}",
                    'League': league,
                    'Outcome': outcome.upper(),
                    'Odd': odd,
                    'EV (%)': ev
                })

    if value_bets:
        st.success(f"Found {len(value_bets)} value bets! Showing top 5:")
        sorted_bets = sorted(value_bets, key=lambda x: x['EV (%)'], reverse=True)
        st.table(sorted_bets[:5])

        pdf_file = generate_pdf(sorted_bets[:5])
        with open(pdf_file, "rb") as file:
            st.download_button(label="📄 Download Top 5 as PDF", data=file, file_name="betmaster_value_bets.pdf")
    else:
        st.warning("No value bets found today.")
