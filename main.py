from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='Overtime Markets Dashboard', layout='wide', page_icon=':dollar:')
st.title("Overtime Markets - Volume")


def clean_data(data_raw):
    for item in data_raw:
        tag = int(item['tags'][0])
        sport_name = ''
        if tag in (9001, 9002): sport_name = 'Football'
        if tag == 9003: sport_name = 'Baseball'
        if tag in (9004, 9005, 9008): sport_name = 'Basketball'
        if tag in (9006,): sport_name = 'Hockey'
        if tag in (9010, 9011, 9012, 9013, 9014, 9015, 9016): sport_name = 'Soccer'
        if tag in (9007,): sport_name = 'UFC'
        item['sport'] = sport_name
    return data_raw


@st.cache(ttl=24 * 60 * 60)
def fetch_names_data():
    payload = {
        "query": """{
              sportMarkets(first: 1000) {
                address
                homeTeam
                awayTeam
                tags
              }
            }""",
    }
    res = requests.post(url='https://api.thegraph.com/subgraphs/name/thales-markets/thales-markets-v2',
                        json=payload).json()['data']['sportMarkets']

    return clean_data(res)


data = fetch_names_data()


@st.cache(ttl=24 * 60 * 60)
def fetch_data(url: str):
    res = requests.get(url=url).json()

    for item in res:
        item['Day'] = datetime.strptime(item['DATE'], '%Y-%m-%d').date()
        item['GAME_ADDRESS'] = item['GAME_ADDRESS']
        item['TAMOUNT'] = int(float(item['TAMOUNT']))
        item['WALLET'] = item['WALLET']

        for jj in data:
            if item['GAME_ADDRESS'] == jj['address']:
                item['sport'] = jj['sport']
                item['game_name'] = f"{jj['homeTeam']} VS {jj['awayTeam']}"
                # break

    return pd.DataFrame(
        res,
        columns=["Day", "GAME_ADDRESS", "TAMOUNT", "WALLET", "sport", "game_name"])


st.markdown("""
Overtime Market is built on top of Thales, which allows users bet on sport games like Football, baseball, Soccer and UFC.
### How it works?
for example there is match tomorrow, i can bet on Team A or B Winning or Draw. for betting i have to Buy the Token which is issued for that match. then after the match if i win, my tokens will worth exactly one dollar,
for example i bought each token for \$0.4, and now they worth \$1, great profit. but if i lose, they worth zero.

### Method:
i use the Flipside data to get the Overtime markets transactions and volume, and because the sport and game labels are not exist on Flipside, i used thegraph.com api to get the labels. \n
then we will look at the last 14 days of Overtime markets stats.
### You Will Read:
1. Total Bet Volume and unique wallets per Sport and Game
2. Top Games by Volume and wallets
3. Volume of each collateral Token (sUSD, USDC, DAI, USDT)
""")
st.markdown("---")
st.write('')
st.write('')
st.markdown("# Sports")

chart_data = fetch_data(
    'https://node-api.flipsidecrypto.com/api/v2/queries/41354585-bc94-4303-bb9f-78934bf5ff9c/data/latest')

c1, c2 = st.columns(2)
total_usd = chart_data.groupby(["sport"], as_index=False).sum()

fig = px.pie(total_usd, values='TAMOUNT', names='sport', title="Total Volume in USD",
             template='ygridoff')
fig.update_traces(textposition='inside', textinfo='value+label', insidetextorientation='radial')
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
c1.plotly_chart(fig, use_container_width=True)

wallets_unique = chart_data.groupby(["sport"], as_index=False).WALLET.nunique()

fig = px.pie(wallets_unique, values='WALLET', names='sport', title="Unique Wallets",
             template='ygridoff')
fig.update_traces(textposition='inside', textinfo='value+label', insidetextorientation='radial')
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
c2.plotly_chart(fig, use_container_width=True)

st.markdown("""
these charts show the the Volume and Unique Wallets per each Sport in the last 14 days, currently four Sports are supported. \n
1. Baseball with 129K dollars, has the highest bet volume, but the number of unique wallets that placed a bet on this sport is 231, which is close to Soccer with 235 wallets.
2. the number of wallets for Soccer and baseball are so close, but soccer total volume is lower than baseball, so bigger bets were placed on Baseball
""")
st.markdown("---")

daily_volume_bar = chart_data.groupby(['Day', 'sport'], as_index=False)['TAMOUNT'].agg('sum')
fig = px.bar(daily_volume_bar, x='Day', y='TAMOUNT', color='sport', title="daily USD Volume", template='seaborn')
fig.update_traces(hovertemplate=None)
fig.update_layout(hovermode="x")
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
this chart shows the daily Volume on each Sport.
1. on August 13th and 14th the volume spiked and increased much higher than the other days. volume peaked at 66K dollars on Aug 14th.
2. by oppening the premier league session and some other invencing programs the volume spiked
3. also overtime markets is in $OP Summer Incentives Projects as you you can see below
""")

tw1 = requests.get('https://publish.twitter.com/oembed?url=https://twitter.com/ETH_Daily/status/1557791609697206277'). \
    json()["html"]
tw2 = \
    requests.get(
        'https://publish.twitter.com/oembed?url=https://twitter.com/OvertimeMarkets/status/1554100781795708929'). \
        json()["html"]
c1, c2 = st.columns(2)
with c1:
    components.html(tw1, height=700)
with c2:
    components.html(tw2, height=700)

st.markdown("---")
st.markdown("# Games")

c1, c2 = st.columns(2)
games_usd = chart_data.groupby(["game_name"], as_index=False).sum()
fig = px.pie(games_usd.sort_values('TAMOUNT', ascending=False).head(10), values='TAMOUNT', names='game_name',
             title="Top Games by USD Volume",
             template='gridon')
fig.update_traces(textposition='inside', textinfo='value+label', insidetextorientation='radial')
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
c1.plotly_chart(fig, use_container_width=True)

games_wallets = chart_data.groupby(["game_name"], as_index=False).WALLET.nunique()
fig = px.pie(games_wallets.sort_values('WALLET', ascending=False).head(10), values='WALLET', names='game_name',
             title="Top Games by Unique Wallets",
             template='gridon')
fig.update_traces(textposition='inside', textinfo='value+label', insidetextorientation='radial')
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
c2.plotly_chart(fig, use_container_width=True)

st.markdown("""
these are the top Games by highest bet volume and wallets engagement.
1. Boston Red Sox vs NY Yankees has the highest volume with 21.5K dollars which is about 7K higher than the second game.
2. also Boston Red Sox vs Baltimore Orioles has the highest number of engaged unique wallets with 54
3. the next games are also between the top teams, for example Manchester United vs Brighton
4. as we saw in upper charts, the Top Games in terms of volume belongs to Baseball sport, but in the terms of wallets, we can see more Soccer games and teams
""")
st.markdown("---")

st.markdown("# Tokens")


@st.cache(ttl=24 * 60 * 60)  # 6 hours
def fetch_tokens_data():
    res = requests.get(
        url='https://node-api.flipsidecrypto.com/api/v2/queries/d84e4333-5633-46a0-83e5-281b8b3074cd/data/latest').json()

    return pd.DataFrame(
        res,
        columns=["SYMBOL", "TAMOUNT", "WALLETS"])


tokens = fetch_tokens_data()
c1, c2 = st.columns(2)

fig = px.pie(tokens, values='TAMOUNT', names='SYMBOL', title="Tokens Total Paid Volume in USD", template='xgridoff')
fig.update_traces(textposition='inside', textinfo='value+label', insidetextorientation='radial')
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
c1.plotly_chart(fig, use_container_width=True)

fig = px.pie(tokens, values='WALLETS', names='SYMBOL', title="Number Unique Wallets paid by each Token",
             template='xgridoff')
fig.update_traces(textposition='inside', textinfo='value+label', insidetextorientation='radial')
fig.update_layout(title_x=0, margin=dict(l=0, r=10, b=30, t=30), yaxis_title=None, xaxis_title=None)
c2.plotly_chart(fig, use_container_width=True)

st.markdown("""
users can do payments with 4 stable coins, sUSD which is the main collateral asset, and USDC, USDT, and DAI. \n
1. most volume is paid with sUSD, which is about 153K dollars, the second token is USDC with 68K dollars 
2. USDT with only 226 dollars is not used much and DAI also has a low volume with 7K dollars.
""")

st.markdown("---")
st.markdown("""
## Conclusion:
1. Baseball with 129K dollars, has the highest bet volume among sports
2. because the number of wallets on baseball and soccer are close and baseball volume is much higher, so bigger bets were placed on Baseball
3. most volume is paid with sUSD
""")

# end
st.write('')
st.write('')
st.write('')
st.write('')
st.write('')
st.markdown("---")
st.markdown("##### Contact:\n"
            "- developed by Misagh lotfi \n"
            "- https://twitter.com/misaghlb \n"
            )

st.markdown("##### Sources:\n"
            "- graph data: https://thegraph.com/hosted-service/subgraph/thales-markets/thales-markets-v2 \n"
            "- https://app.flipsidecrypto.com/velocity/queries/d84e4333-5633-46a0-83e5-281b8b3074cd  \n"
            "- https://app.flipsidecrypto.com/velocity/queries/41354585-bc94-4303-bb9f-78934bf5ff9c  \n"
            "- code: https://github.com/Misaghlb/overtimemarkets_volume_streamlit \n"
            )
