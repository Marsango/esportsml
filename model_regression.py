import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.linear_model import ElasticNet
import pickle

def calculate_precision_percent(predict, y_test, arbitrary_value):
    hitted = 0
    count_bets = 0
    for j, value in enumerate(y_test):
        if round(predict[j]) > arbitrary_value + 2:
            if value > arbitrary_value:
                hitted += 1
            count_bets += 1
        elif round(predict[j]) < arbitrary_value - 2:
            if value < arbitrary_value:
                hitted += 1
            count_bets += 1
    return hitted/count_bets*100

def calculate_units_gaineds(predict, y_test, meankills):
    units = 0
    number_of_bets = 0
    hitted = 0
    over = [0, 0]
    under = [0, 0]
    bets = []
    index = y_test.index
    for j, value in enumerate(y_test):
        key = index[j]
        line = round(28.5)
        ai_hint = round(predict[j])
        if ai_hint > line + 2.5:
            if value > line:
                units += 0.83
                hitted += 1
                over[1] += 1
            else:
                units -= 1
            over[0] += 1
            number_of_bets += 1
        elif ai_hint < line - 2.5:
            if value < line:
                units += 0.83
                hitted += 1
                under[1] += 1
            else:
                units -= 1
            under[0] += 1
            number_of_bets += 1

    if number_of_bets != 0:
        return units, number_of_bets, hitted/number_of_bets*100, bets, over, under
    else:
        return units, number_of_bets, hitted / (number_of_bets + 1), bets, over, under


def fit_model():
    dataset = pd.read_csv('dataset_top_leagues_reg_l10.csv')
    X = dataset.drop(['Tendency', 'killsat15', 'numberofgames', "melee_number", 'MeanKills', 'killsat10'], axis=1)
    normalized_x = (X - X.min()) / (X.max() - X.min())
    y = dataset['Tendency']
    X_train, X_test, y_train, y_test = train_test_split(normalized_x, y, test_size=0.2, random_state=42)
    model = ElasticNet(alpha=0.1, l1_ratio=1)
    model.fit(X_train, y_train)
    predict = model.predict(X_test)
    units_gained_by_model = calculate_units_gaineds(predict, y_test, 28.5)
    for bet in units_gained_by_model[3]:
        print(f'{bet}')
        print(f'Units: {units_gained_by_model[0]}\nNumber of bets: {units_gained_by_model[1]}\n{units_gained_by_model[2]}% de Acerto')
    with open('model_normalized_meankills.pkl','wb') as f:
        pickle.dump(model,f)
    print(r2_score(y_test, predict))

fit_model()