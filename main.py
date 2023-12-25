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

df = pd.read_csv("Proje/2022-01-08.csv")

grouped_by_id = pd.read_csv("Proje/grouped_by_id.csv")

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
