import requests
from datetime import datetime

# 🔐 API Setup
API_KEY = '1f0e3a6f6e8437ada8118c3ac27bb2e5'
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {'x-apisports-key': API_KEY}

# ✅ Get today's fixtures
def get_all_fixtures_today():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={today}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get('response', [])

# ✅ Get odds for one fixture
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
    except Exception as e:
        print("⚠️ Odds parsing error:", e)
    return None

# 🔍 Get next match info for a team
def get_next_fixture(team_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&next=1"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if data['response']:
            next_game = data['response'][0]
            opponent = next_game['teams']['away']['name'] if next_game['teams']['home']['id'] == team_id else next_game['teams']['home']['name']
            date = next_game['fixture']['date']
            return {"opponent": opponent, "date": date}
    return None

# 🧠 Analyze all matches
def analyze_all_matches():
    fixtures = get_all_fixtures_today()
    print(f"\n📅 Total matches today: {len(fixtures)}")

    value_bets_list = []

    for match in fixtures:
        fixture_id = match['fixture']['id']
        home_team = match['teams']['home']
        away_team = match['teams']['away']
        home = home_team['name']
        away = away_team['name']
        home_id = home_team['id']
        away_id = away_team['id']
        time = match['fixture']['date'][11:16]
        league = match['league']['name']

        odds = get_odds_for_fixture(fixture_id)
        if not odds:
            continue

        for outcome, odd in odds.items():
            if odd == 0:
                continue
            implied_prob = 1 / odd
            ev = (implied_prob * 100) - 100
            note = ""

            # 🔍 Add rotation risk note if next match is tougher (mock logic)
            if outcome.lower() == 'home':
                next_game = get_next_fixture(home_id)
                if next_game:
                    note = f"🧠 {home}'s next game is vs {next_game['opponent']} — may affect lineup."
            elif outcome.lower() == 'away':
                next_game = get_next_fixture(away_id)
                if next_game:
                    note = f"🧠 {away}'s next game is vs {next_game['opponent']} — may affect lineup."

            if ev > 0:  # ✅ Only show true positive EV bets
                value_bets_list.append({
                    'match': f"{home} vs {away}",
                    'league': league,
                    'time': time,
                    'outcome': outcome.upper(),
                    'odd': odd,
                    'ev': round(ev, 2),
                    'implied_prob': round(implied_prob * 100, 2),
                    'note': note
                })

    if not value_bets_list:
        print("\n⚠️ No value bets found today (EV > 0).")
        return

    value_bets_list.sort(key=lambda x: x['ev'], reverse=True)

    print(f"\n💰 Top {min(5, len(value_bets_list))} Value Bets for Today:\n")
    for bet in value_bets_list[:5]:
        print(f"⚔️ {bet['match']} @ {bet['time']} ({bet['league']})")
        print(f"💡 Bet: {bet['outcome']} @ {bet['odd']} | EV: {bet['ev']}% | Implied: {bet['implied_prob']}%")
        if bet['note']:
            print(f"📌 Note: {bet['note']}")
        print("-" * 50)

# 🚀 Run
if __name__ == "__main__":
    analyze_all_matches()