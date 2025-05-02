import csv
import statistics
import traceback
from datetime import datetime
from mwrogue.esports_client import EsportsClient
import json
from format_database import running_program, reading_dataset, get_tournament_split

loldb = EsportsClient("lol")
range_dict = {}


def create_range_dict():
    response = loldb.cargo_client.query(
        tables="Champions=C",
        fields=f"C.Name, C.AttackRange",
    )
    for r in response:
        if r["Name"] == 'Nunu &amp; Willump':
            r["Name"] = 'Nunu'
        range_dict[f'{r["Name"]}'] = r['AttackRange']


def normalizing_champions_to_delta(champions):
    file2 = open('./datasets/champions_mean.json', encoding="utf8")
    data_champion = json.load(file2)
    for i, z in enumerate(champions):
        if i == 0:
            var = '_top'
        elif i == 1:
            var = '_jungle'
        elif i == 2:
            var = '_mid'
        elif i == 3:
            var = '_adc'
        elif i == 4:
            var = '_sup'
        try:
            if data_champion[f'{champions[i].lower()}{var}'][1] < 20:
                champions[i] = 0
            else:
                champions[i] = data_champion[f'{champions[i].lower()}{var}'][0]
        except:
            champions[i] = 0


def teams_exceptions(team):
    if team == 'Beşiktaş Esports':
        return 'BeÅŸiktaÅŸ Esports'
    elif team == 'Barça eSports':
        return 'BarÃ§a eSports'
    else:
        return team


def calculate_tendency(TotalKills, teamA, teamB):
    try:
        kills_median = (teamA + teamB) / 2
        if TotalKills > (kills_median - 0.5):
            return 'over'
        else:
            return 'under'
    except:
        print('bug')
        return 'bugou'


def calculate_total_melees(champions1, champions2):
    total_melee = -4
    champions = champions1 + champions2
    for champion in champions:
        if int(range_dict[champion]) < 425:
            total_melee += 1
    return total_melee

def get_median_for_means(games_before, stats, normalized_means):
    normalized_means[stats] = statistics.median([x[stats] for x in games_before])

def calculate_means(date, team, lastX, split):
    f = open('./datasets/teams_means.json', encoding="utf8")
    data = json.load(f)
    games_before = [x for x in data[team + f'_{date.year}_split{split}'] if datetime.strptime(x['date'], '%Y-%m-%d').date() < date]
    games_before = sorted(games_before, key=lambda d: d['date'],  reverse=True)
    if lastX != -1:
        games_before = games_before[:lastX]
    normalized_means = {}
    if games_before:
        for game in games_before:
            for key in game:
                if key != 'date':
                    get_median_for_means(games_before, key, normalized_means)
    return normalized_means, len(games_before)


def generate_csv(response, leagues, prediction_type, lastX):
    with open(f'dataset_{leagues}_leagues_{prediction_type}_l{lastX}.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        field = ["Tendency", "TOP1", "JG1", "MID1", "AD1", "SUP1", "TOP2", "JG2", "MID2", "AD2", "SUP2", "melee_number",
                 "MeanKills", "killsat10", "killsat15", "numberofgames"]
        if prediction_type == 'clf':
            field.pop('MeanKills')
        writer.writerow(field)
        df_date = datetime.strptime(response[0]['DateTime UTC'].split()[0], '%Y-%m-%d').date()
        df = reading_dataset(df_date.year)
        for db_row in response:
            try:
                date = datetime.strptime(db_row['DateTime UTC'].split()[0], '%Y-%m-%d').date()
                if date.year != df_date.year:
                    df_date = date
                    df = reading_dataset(date.year)
                if date.year != 2024:
                    continue
                split = get_tournament_split(db_row['Name'])
                if split != 1:
                    continue
                game_mean_statsA = calculate_means(date, db_row['Team1'], lastX, split)
                game_mean_statsB = calculate_means(date, db_row['Team2'], lastX, split)
                if game_mean_statsB[1] < 5 or game_mean_statsA[1] < 5:
                    continue
                df_match = df.query(f'gameid == "{db_row["RiotPlatformGameId"]}"')
                if df_match['killsat10'].values.size == 0:
                    continue
                killsat10 = (df_match['killsat10'].values[0] + df_match['opp_killsat10'].values[0]) - (game_mean_statsA[0]['kills_at_10'] + game_mean_statsB[0]['kills_at_10'])/2
                killsat15 = (df_match['killsat15'].values[0] + df_match['opp_killsat15'].values[0]) - (game_mean_statsA[0]['kills_at_15'] + game_mean_statsB[0]['kills_at_15'])/2
                champions1 = db_row['Team1Picks'].split(',')
                champions2 = db_row['Team2Picks'].split(',')
                total_melees = calculate_total_melees(champions1, champions2)
                normalizing_champions_to_delta(champions1)
                normalizing_champions_to_delta(champions2)
                if prediction_type == 'clf':
                    tendency = calculate_tendency(int(db_row['Team1Kills']) + int(db_row['Team2Kills']), game_mean_statsA[0]['total_kills'], game_mean_statsB[0]['total_kills'])
                else:
                    tendency = int(db_row['Team1Kills']) + int(db_row['Team2Kills'])
                row = [f"{tendency}", (champions1[0] + champions1[0])/2, (champions1[1] + champions1[1])/2,
                       (champions1[2] + champions1[2])/2,
                       (champions1[3] + champions2[3])/2,
                       (champions1[4] + champions2[4])/2, total_melees]
                if prediction_type == 'reg':
                    row.append((game_mean_statsA[0]['total_kills']+game_mean_statsB[0]['total_kills'])/2)
                row.append(killsat10)
                row.append(killsat15)
                row.append(int((game_mean_statsA[1] + game_mean_statsB[1])/2))
                writer.writerow(row)
            except TypeError:
                continue
            except Exception:
                traceback.print_exc()



if __name__ == '__main__':
    create_range_dict()
    leagues = input('EMEA (EMEA), Top Leagues (TOP) or Wildcard (WC): ').lower()
    predicition_type = input('REGRESSION (REG) OR CLASSIFICATION (CLF): ').lower()
    response = running_program(leagues)
    last_x_options = [10]
    for last_x in last_x_options:
        generate_csv(response, leagues, predicition_type, last_x)