import streamlit as st
import pandas as pd

pd.set_option('display.width', 50000)
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.4f' % x)

st.set_page_config(layout="wide")

html_temp = """
<div style="background-color:tomato;padding:1.5px">
<h1 style="color:white;text-align:center;">Top 20 Board Games ⬆⬇ </h1>
</div><br>"""
st.markdown(html_temp, unsafe_allow_html=True)

tab_1, tab_2, tab_3 = st.tabs(["Top 20", "Oyun Tavsiyesi", "Makine Öğrenmesi"]) # Deneme için koydum.

df = pd.read_csv("2022-01-08.csv")

grouped_by_id = pd.read_csv("grouped_by_id.csv")

# URL yarım geldiği için baş kısmını tamamlıyoruz. Bunu daha sonra fotoğrafların içine köprü için kullanacağız.
df["URL-ek"] = "https://boardgamegeek.com/"

df["Link"] = df["URL-ek"] + df["URL"]

del df["URL-ek"]

# Bar score için dataframe birleştirme
merged_df = pd.merge(grouped_by_id, df[["ID", "Bayes average", "Rank", "Name", "Link", "Thumbnail"]], "right","ID")


M = 1000
C = merged_df['avg_rating'].mean()  # 6.08

def weighted_rating(r, v, M, C):
    return (v / (v + M) * r) + (M / (v + M) * C)

merged_df["weighted_rating"] = weighted_rating(merged_df["avg_rating"], merged_df["rating_count"], M, C)

# Hybrid sorting
def hybrid_sorting_score(bar_score, wss_score, bar_w=60, wss_w=40):
    return bar_score*bar_w/100 + wss_score*wss_w/100

M = 1000
C = merged_df['avg_rating'].mean()  # 6.08
bar_score = merged_df["Bayes average"]
wss_score = weighted_rating(merged_df["avg_rating"], merged_df["rating_count"], M, C)


merged_df["hybrid_sorting_score"] = hybrid_sorting_score(bar_score, wss_score)


top_games = merged_df.sort_values("hybrid_sorting_score", ascending=False).reset_index(drop=True)
top_games.index = top_games.index +1

top_games.head(20)


# Streamlit
column_left, column_right = tab_1.columns(2)

# Left Column
column_left.header("Bizim Sıralama")
column_left.dataframe(top_games[["ID", "Name", "Bayes average","avg_rating", "rating_count","hybrid_sorting_score"]].head(20), width=2000, height=385)

real_rank = merged_df.sort_values("Rank", ascending=True).reset_index(drop=True)
real_rank.index = real_rank.index +1

# Right Column
column_right.header("BGG Sıralama")
column_right.dataframe(real_rank[["ID", "Name", "Bayes average","avg_rating", "rating_count","hybrid_sorting_score"]].head(20), width=2000, height=385)

selected_game = tab_1.selectbox(label="Oyun Seçiniz", options=top_games.Name.unique())
selected_game_info = top_games[top_games["Name"] == selected_game].iloc[0]

filtered_games = top_games[top_games.Name == selected_game]
filtered_games2 = real_rank[real_rank.Name == selected_game]


message1 = f"{selected_game} oyununun sıralaması: {filtered_games.index[0]}"
column_left.success(message1)

tab_1.markdown(f'<a href="{selected_game_info["Link"]}" target="_blank"><img src="{selected_game_info["Thumbnail"]}" style="width:200px;"></a>', unsafe_allow_html=True)


message2 = f"{selected_game} oyununun sıralaması: {filtered_games2.index[0]}"

if filtered_games.index[0] == filtered_games2.index[0]:
    column_right.success(message2)
elif 0 < abs(filtered_games.index[0] - filtered_games2.index[0]) < 4:
    column_right.warning(message2)
else:
    column_right.error(message2)


# modele beslemek için gerekli seçimleri yap
tab_ml.markdown("<h1 style='text-align: center; '>Oyununuz için değerleri seçiniz</h1>", unsafe_allow_html=True)

# sütunlara ayır
column_one, column_two, column_three = tab_ml.columns([3, 3, 3], gap="small")


def load_model():
    return joblib.load("bgmodel_.joblib")
model = load_model()

def user_input_features():
    subcategories = ["Savas", "Bilgi", "Macera", "Strateji", "Puzzle", "Sosyal", "Sanat", "Rekabetçi"]
    selected_subcategories = column_one.multiselect("Select subcategories:", subcategories)
    subcategories_df = pd.DataFrame(columns=subcategories)
    subcategories_df.loc[0] = [0] * len(subcategories)
    for subcategory in selected_subcategories:
        if subcategory in subcategories_df.columns:
            subcategories_df.at[0, subcategory] = 1
    return subcategories_df

def categorize_game(min_age, average_weight, max_players, max_playtime):
    if (min_age <= 7 and average_weight < 3.5):
        return "Children's_Game"
    elif max_players >= 6 and average_weight <= 2:
        return "Party_Game"
    elif average_weight <= 2 and min_age <= 13 and max_playtime <= 90:
        return "Family_Game"
    elif average_weight > 3.5:
        return "Heavy_Game"
    elif average_weight > 2:
        return "Strategy_Game"
    else:
        return "Family_Game"

min_age = column_one.number_input('Minimum Yaş', min_value=0, value=0, step=1)
min_players = column_two.number_input('Minimum Oyuncu Sayısı', min_value=0, value=0, step=1)
max_players = column_three.number_input('Maksimum Oyuncu Sayısı', min_value=0, value=0, step=1)
max_playtime = column_three.number_input('Oyun Süresi (dakika)', min_value=0, value=0, step=1)
average_weight = column_two.slider('Karmaşıklık', 0.0, 5.0, 0.0)


game_category = categorize_game(min_age, average_weight, max_players, max_playtime)
categories = ["Children's_Game", "Party_Game", "Family_Game", "Heavy_Game", "Strategy_Game"]
category_df = pd.DataFrame(columns=categories)
category_df.loc[0] = [0] * len(categories)
category_df.at[0, game_category] = 1
category_df = category_df.drop("Children's_Game", axis=1)

def categorize_playtime(max_playtime):
    if 0 <= max_playtime <= 30:
        return "Kisa"
    elif 30 < max_playtime <= 60:
        return "Orta"
    elif 60 < max_playtime <= 120:
        return "Uzun"
    else:
        return "Cok uzun"

def categorize_age(min_age):
    if min_age < 7:
        return "0-6"
    elif min_age < 10:
        return "7-10"
    elif min_age < 13:
        return "10-13"
    elif min_age < 18:
        return "13-18"
    else:
        return "+18"

# Additional inputs and one-hot encoding
playtime_category = categorize_playtime(max_playtime)
age_category = categorize_age(min_age)

playtime_categories = ["Kisa", "Orta", "Uzun", "Cok uzun"]
age_categories = ["0-6", "7-10", "10-13", "13-18", "+18"]

playtime_df = pd.DataFrame(columns=playtime_categories)
age_df = pd.DataFrame(columns=age_categories)

playtime_df.loc[0] = [0] * len(playtime_categories)
age_df.loc[0] = [0] * len(age_categories)

playtime_df.at[0, playtime_category] = 1
playtime_df = playtime_df.drop("Cok uzun", axis=1)
age_df.at[0, age_category] = 1
age_df = age_df.drop("+18", axis=1)

subcategories_df = user_input_features()
combined_df = pd.concat([subcategories_df, category_df, playtime_df, age_df], axis=1)

tab_ml = tab_ml.container()
tab_ml.write("# Puan Tahmini")
input_df = combined_df

if tab_ml.button('Tahmin Et'):
    prediction = model.predict(input_df)
    tab_ml.write("Oyunun tahmin edilen puanı:")
    tab_ml.write(prediction[0])
