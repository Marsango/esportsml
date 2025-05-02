from mwrogue.esports_client import EsportsClient
import json
import statistics
from datetime import datetime
import pandas as pd
import traceback

loldb = EsportsClient("lol")
champions_dict = {}
champions_mean_dict = {}
teams_dict = {}
year_start = '2024'
year_end = '2025'
split = f"SG.DateTime_UTC >= '{year_start}-01-01 00:00:00' AND SG.DateTime_UTC <= '{year_end}-12-31 00:00:00'"

def reading_dataset(year):
    df = pd.read_csv(f'./datasets/oracledb_{year}.csv')
    filtered_df = df[df['opp_assistsat15'].notna()]
    filtered_df = filtered_df[filtered_df['position'] == 'team']
    filtered_df = filtered_df.drop_duplicates(subset=['gameid'], keep='first')
    return filtered_df

def create_champions_dict():
    response = loldb.cargo_client.query(
        tables="Champions=C",
        fields=f"C.Name",
    )
    for r in response:
        if r["Name"] == 'Nunu &amp; Willump':
            r["Name"] = 'Nunu'
        for i in range(1, 6):
            champions_dict[f'{r["Name"]}{i}'] = []


def get_stats_from_db():  ## pensar em puxar bonecos que mais e menos morrem, mais matam e menos matam
    response = loldb.cargo_client.query(
        tables="ScoreboardGames=SG, Tournaments=T",
        join_on="SG.OverviewPage=T.OverviewPage",
        fields=f"SG.Team1Picks, SG.Team2Picks, SG.Team1Kills, SG.Team2Kills, SG.Team1, SG.Team2, T.Name, SG.DateTime_UTC, SG.RiotPlatformGameId",
        where=f"{split}"
    )
    response.sort(key=lambda x: x['DateTime UTC'].split('-'))
    return response

def create_teams_dict(team):
    if team not in teams_dict.keys():
        teams_dict[team] = []

def update_teams_dict(team, kills, killsat10, goldleadat10, killsat15, date):
    if team not in teams_dict.keys():
        teams_dict[team] = []
    teams_dict[team].append({'total_kills' : kills, 'gold_at_10': goldleadat10, 'kills_at_10' : killsat10, 'kills_at_15' : killsat15,'date': date})


def get_mean_kills_team(team):
    return statistics.median([x['total_kills'] for x in teams_dict[team]])


def set_champions_kills(picks, kills, teamA, teamB):
    i = 1
    for pick in picks:
        if len(teams_dict[teamA]) < 5 or len(teams_dict[teamB]) < 5:
            return
        champions_dict[f'{pick}{i}'].append(kills - (get_mean_kills_team(teamA) + get_mean_kills_team(teamB)) / 2)
        i += 1


def replace_number_by_lane(champion):
    if '1' in champion:
        champion = champion.replace('1', '_TOP')
    elif '2' in champion:
        champion = champion.replace('2', '_JUNGLE')
    elif '3' in champion:
        champion = champion.replace('3', '_MID')
    elif '4' in champion:
        champion = champion.replace('4', '_ADC')
    elif '5' in champion:
        champion = champion.replace('5', '_SUP')
    return champion


def get_mean_kills_champion():
    for champion in champions_dict:
        if champions_dict[champion]:
            champion_lane = replace_number_by_lane(champion)
            champions_mean_dict[champion_lane.lower()] = [statistics.median(champions_dict[champion]),
                                                          len(champions_dict[champion])]





def output_json():
    data = teams_dict
    with open('./datasets/teams_means.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)
    data = champions_mean_dict
    with open('./datasets/champions_mean.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def do_a_treatment_of_database(response, leagues):  ##testar sem avoid_leagues, só 2024
    new_response = []
    query_leagues = []
    ligas = leagues
    for year in range(int(year_start), int(year_end) + 1):
        if ligas == 'emea':
            query_leagues += [f"Ultraliga {year}",
                              f"Elite Series {year}",
                              f"NLC {year}",
                              f"LIT {year}",
                              f"TCL {year}",
                              f"LPLOL {year}",
                              f"Hitpoint Masters {year}",
                              f"EBL {year}",
                              f"Prime League 1st Division {year}",
                              f"EMEA Masters {year}GLL {year}",
                              f"LFL {year}",
                              f"LVP SL {year}",
                              f"Arabian League {year}"]
        elif ligas == 'wc':
            query_leagues += [
                f"LJL {year}",
                f"LLA {year}",
                f"LCO {year}",
                f"PCS {year}",
                f"VCS {year}",
                f"CBLOL {year}"]
        elif ligas == 'top':
            query_leagues += [
                f"LCS {year}",
                f"LEC {year}",
                f"LPL {year}",
                f"LCK {year}",
                f"MSI {year}",
                f"WORLDS {year}"
            ]
        elif ligas == 'all':
            query_leagues += [f"Ultraliga {year}",
                              f"Elite Series {year}",
                              f"NLC {year}",
                              f"LIT {year}",
                              f"TCL {year}",
                              f"LPLOL {year}",
                              f"Hitpoint Masters {year}",
                              f"EBL {year}",
                              f"PRM 1st Division {year}",
                              f"EMEA Masters {year}",
                              f"GLL {year}",
                              f"LFL {year}",
                              f"LVP SL {year}",
                              f"Arabian League {year}",
                              f"LJL {year}",
                              f"LLA {year}",
                              f"LCO {year}",
                              f"PCS {year}",
                              f"VCS {year}",
                              f"CBLOL {year}",
                              f"LCS {year}",
                              f"LEC {year}",
                              f"LPL {year}",
                              f"MSI {year}",
                              f"WORLDS {year}",
                              f"LCK {year}"
                              ]
    for res in response:
        for league in query_leagues:
            if league in res['Name']:
                new_response.append(res)
    return new_response

def get_tournament_split(tournament):
    tournament = tournament.lower()
    if 'split 1' in tournament or 'spring' in tournament or 'msi' in tournament:
        return 1
    elif 'split 2' in tournament or 'summer' in tournament or 'worlds' in tournament:
        return 2
    else:
        return -1
def iterate_over_oracle(df, gameid):
    df_match = df.query(f'gameid == "{gameid}"')
    if df_match['killsat10'].values.size == 0 or df_match['golddiffat10'].values.size == 0:
        return None, None, None
    golddiffat10 = abs(df_match['golddiffat10'].values[0])
    killsat10 = df_match['killsat10'].values[0] + df_match['opp_killsat10'].values[0]
    killsat15 = df_match['killsat15'].values[0] + df_match['opp_killsat15'].values[0]
    return golddiffat10, killsat10, killsat15

def iterate_over_database(database):
    df_date = datetime.strptime(database[0]['DateTime UTC'].split()[0], '%Y-%m-%d').date()
    df = reading_dataset(df_date.year)
    for res in database:
        date = datetime.strptime(res['DateTime UTC'].split()[0], '%Y-%m-%d').date()
        if date.year != df_date.year:
            df_date = date
            df = reading_dataset(date.year)
        try:
            split = get_tournament_split(res['Name'])
            teamA = res[f'Team1'] + f'_{date.year}_split{split}'
            teamB = res[f'Team2'] + f'_{date.year}_split{split}'
            total_kills_game = int(res['Team1Kills']) + int(res['Team2Kills'])
            create_teams_dict(teamA)
            create_teams_dict(teamB)
            for i in range(1, 3):
                picks = res[f'Team{i}Picks'].split(',')
                set_champions_kills(picks, total_kills_game, teamA, teamB)
            oracle_infos = iterate_over_oracle(df, res['RiotPlatformGameId'])
            golddiffat10, killsat10, killsat15 = oracle_infos[0], oracle_infos[1], oracle_infos[2]
            update_teams_dict(teamA, total_kills_game, killsat10, golddiffat10, killsat15, date)
            update_teams_dict(teamB, total_kills_game, killsat10, golddiffat10, killsat15, date)
        except Exception:
            traceback.print_exc()
            continue


def running_program(leagues):
    create_champions_dict()
    database = do_a_treatment_of_database(get_stats_from_db(), leagues)
    iterate_over_database(database)
    get_mean_kills_champion()
    output_json()
    return database


