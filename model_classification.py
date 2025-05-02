import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import SVC


def calculate_units_gaineds(current_proba, model):
    class_names = model.classes_
    units = 0
    number_of_bets = 0
    hitted = 0
    bets = []
    for j, key in enumerate(y_test):
        highest_number = 0
        position = 0
        betting_x = 0
        for i, number in enumerate(current_proba[j]):
            if number > highest_number:
                position = i
                highest_number = number
        prediction = class_names[position]
        if 0.5445 < highest_number < 0.70:
            betting_x = 1
            number_of_bets += 1
        elif 0.70 < highest_number:
            betting_x = 2
            number_of_bets += 1
        if key == prediction and betting_x != 0:
            units += betting_x * 0.83
            hitted += 1
            bets.append([betting_x, prediction, highest_number, key])
        elif betting_x != 0:
            units -= betting_x
            bets.append([betting_x, prediction, highest_number, key])
    if number_of_bets != 0:
        return units, number_of_bets, hitted/number_of_bets*100, bets
    else:
        return units, number_of_bets, hitted / (number_of_bets + 1), bets


# Carregando o dataset
dataset = pd.read_csv('dataset_allleagues.csv')

# Dividindo features e alvo
X = dataset.drop('Tendency', axis=1)
y = dataset['Tendency']

# Codificando one-hot para os campeões
encoder = OneHotEncoder()
X_encoded = encoder.fit_transform(X)

# Dividindo em conjuntos de treinamento e teste
X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)

# Obtendo todos os estimadores de classificação disponíveis
model = SVC(decision_function_shape = 'ovo', gamma = 'scale', kernel = 'sigmoid', probability = True, tol = 0.0001)
model.fit(X_train, y_train)
units_gained_by_model = calculate_units_gaineds(model.predict_proba(X_test), model)
y_pred = model.predict(X_test)
report = classification_report(y_test, y_pred, output_dict=True)
for bet in units_gained_by_model[3]:
    print(f'{bet}')
print(report)
print(f'Units: {units_gained_by_model[0]}\nNumber of bets: {units_gained_by_model[1]}\n{units_gained_by_model[2]}% de Acerto')