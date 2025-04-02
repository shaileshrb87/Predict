from flask_cors import CORS
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
import json

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Load datasets
head_to_head_df = pd.read_csv("head_to_head_data_100rows.csv")
player_performance_df = pd.read_csv("player_performance_data_corrected.csv")
college_cricket_stats_df = pd.read_csv("college_cricket_stats.csv")
match_data_df = pd.read_csv("match_data_cleaned.csv")

# Clean head-to-head data
head_to_head_agg = (
    head_to_head_df
    .groupby(['Team_A', 'Team_B'])
    .agg({'Team_A_Win_Rate': 'mean', 'Total_Matches': 'sum'})
    .reset_index()
)

# Function to get team features
def get_team_features(team, opponent):
    dept_stats = college_cricket_stats_df[college_cricket_stats_df['Department'] == team].iloc[0]
    players = player_performance_df[
        (player_performance_df['Department'] == team) & 
        (player_performance_df['Status'] == 'Active')
    ]
    team_bat_avg = players['Batting_Average'].mean()
    team_strike_rate = players['Strike_Rate'].mean()
    team_wicket_takers = players[players['Wickets_Taken'] > 0]['Wickets_Taken'].mean()

    h2h = head_to_head_agg[
        (head_to_head_agg['Team_A'] == team) & 
        (head_to_head_agg['Team_B'] == opponent)
    ]
    h2h_rate = h2h['Team_A_Win_Rate'].values[0] if not h2h.empty else 0.5
    h2h_weight = np.log1p(h2h['Total_Matches'].values[0]) if not h2h.empty else 0
    return [
        dept_stats['Win_Rate'],
        team_bat_avg,
        team_strike_rate,
        team_wicket_takers,
        h2h_rate * h2h_weight
    ]

# Prepare dataset
data = []
for _, row in match_data_df.iterrows():
    team_a, team_b = row['Team_A'], row['Team_B']
    team_a_features = get_team_features(team_a, team_b)
    team_b_features = get_team_features(team_b, team_a)
    toss_winner = 1 if row['Toss_Winner'] == team_a else 0
    target = 1 if row['Winner'] == team_a else 0
    data.append(team_a_features + team_b_features + [toss_winner, target])

columns = [
    'Team_A_Win_Rate', 'Team_A_Bat_Avg', 'Team_A_Strike_Rate', 'Team_A_Wickets', 'Team_A_H2H',
    'Team_B_Win_Rate', 'Team_B_Bat_Avg', 'Team_B_Strike_Rate', 'Team_B_Wickets', 'Team_B_H2H',
    'Toss_Winner', 'Winner'
]
data_df = pd.DataFrame(data, columns=columns)

# Train-test split
X = data_df.drop(columns=['Winner'])
y = data_df['Winner']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Model training
model = xgb.XGBClassifier(
    max_depth=3,
    learning_rate=0.05,
    n_estimators=200,
    reg_alpha=0.5,
    reg_lambda=1.0,
    eval_metric='logloss'
)
model.fit(X_train, y_train)

calibrated_model = CalibratedClassifierCV(model, cv=5, method='isotonic')
calibrated_model.fit(X_train, y_train)

# Prediction endpoint
# In prediction.py's /predict endpoint
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    team_a = data['teamA']
    team_b = data['teamB']
    toss_winner = data['tossWinner']

    # Add validation
    if toss_winner not in [team_a, team_b]:
        return jsonify({"error": "Invalid toss winner selection"}), 400

    # Reverse team order if needed
    if toss_winner == team_b:
        # Swap teams to maintain consistent perspective
        team_a, team_b = team_b, team_a
        is_swapped = True
    else:
        is_swapped = False

    team_a_features = get_team_features(team_a, team_b)
    team_b_features = get_team_features(team_b, team_a)
    toss = 1  # Now always 1 since we swapped teams if needed

    features = np.array([team_a_features + team_b_features + [toss]])
    prob = calibrated_model.predict_proba(features)[0][1]

    # Adjust winner based on swap
    final_winner = team_a if prob > 0.5 else team_b
    if is_swapped:
        final_winner = team_b if final_winner == team_a else team_a

    return jsonify({
        "predicted_winner": final_winner,
        "confidence": round(max(prob, 1-prob) * 100, 2)
    })

if __name__ == '__main__':
    app.run(port=5001)
