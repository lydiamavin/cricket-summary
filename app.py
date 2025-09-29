import streamlit as st
from src.main import generate_comic
from dotenv import load_dotenv

load_dotenv()

st.title("Cricket Comic Strip Generator")

tournament_name = st.text_input("Tournament Name", "IPL 2023")
match_round = st.text_input("Match Round", "Final")
match_date = st.date_input("Match Date")
toss_winner = st.text_input("Toss Winner", "India")
team1_score = st.text_input("Team 1 Final Score", "India 250/5")
team2_score = st.text_input("Team 2 Final Score", "Australia 245/7")
result = st.text_input("Result", "India won by 5 wickets")
summary = st.text_area("Summary", "Virat Kohli scored a brilliant century off 50 balls. Mitchell Starc took 3 wickets early. India chased down the target in the last over with a six.")

if st.button("Generate Comic Strip"):
    data = {
        "tournament_name": tournament_name,
        "match_round": match_round,
        "match_date": str(match_date),
        "toss_winner": toss_winner,
        "final_scores": {
            "team1": team1_score,
            "team2": team2_score
        },
        "result": result,
        "summary": summary
    }
    generate_comic(data)
    st.image("comic.png")