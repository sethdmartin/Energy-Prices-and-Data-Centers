# -*- coding: utf-8 -*-
"""
Created on Sat Nov  8 11:40:53 2025

@author: Seth
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patheffects as pe
import re

'''
Examination of correlations between data center power usage and price changes for residential
Initial visualization: plot map of USA, color code by electricity price changes, overlay data center power usage stats

might open up into PCA on various columns from these sets
'''

###
###DATA
###

df_energy_prc_mo=pd.read_excel('energy data/price/retail_price_monthly.xlsx')
df_energy_sal_mo=pd.read_excel('energy data/price/sales_monthly.xlsx')
df_energy_rev_mo=pd.read_excel('energy data/price/revenue_monthly.xlsx')
'''
Setup of price data:
Extracting residential and industrial prices for '24, '25, for states only
calculating difference in residential vs insustrial price changes as 'spread'
higher spread means cost changes favored industrial purchasers over residential
in many states residential prices rise to subsidize price lowering for industrial facilities

later on: comparing this spread value to total and fractional data center power consumption
'''
col_nms=['Table 5.6.A. Average Price of Electricity to Ultimate Customers by End-Use Sector,','Unnamed: 1','Unnamed: 2',\
        'Unnamed: 5','Unnamed: 6']
col_mngs=['state','res_25','res_24','ind_25','ind_24']

col_nms_sal=['Table 5.4.B. Sales of Electricity to Ultimate Customers by End-Use Sector,','Unnamed: 9']
#power sales in GWh, total all-sector consumption over 2025
col_mngs_sal=['state','total usage']

states = np.array([
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming"
])

#setting up df
df_en_prc_cut = df_energy_prc_mo.loc[
    df_energy_prc_mo[col_nms[0]].isin(states),  
    col_nms  
]
df_en_prc_cut.columns=col_mngs
delta_res=df_en_prc_cut['res_25']-df_en_prc_cut['res_24']
delta_ind=df_en_prc_cut['ind_25']-df_en_prc_cut['ind_24']
df_en_prc_cut.insert(3, 'delta_res',delta_res)
df_en_prc_cut.insert(6, 'delta_ind',delta_ind)
df_en_prc_cut.insert(7, 'spread',delta_res-delta_ind)

spread = df_en_prc_cut['spread']
states = df_en_prc_cut['state']
data = pd.DataFrame({
    "state": states,
    "spread": spread,
    "delta_res": delta_res
})

df_sal_cut=df_energy_sal_mo.loc[
    df_energy_sal_mo[col_nms_sal[0]].isin(states),
    col_nms_sal
]
df_sal_cut.columns=col_mngs_sal
data=data.merge(df_sal_cut,left_on='state',right_on='state',how='left')

#data on total datacenter power usage from: https://www.electricchoice.com/blog/datacenters-electricity/
text_pw_us = """
state    1    1 Twh    Smwr
Virginia    1,000    23 TWh    Ashburn ("Data Center Alley"), Loudoun County | AWS, Microsoft, Google, Equinix, Digital Realty
Texas    450    16 TWh    Dallas-Fort Worth, Austin, Houston | Meta, Google, CyrusOne, Switch, Digital Realty
California    350    11 TWh    Silicon Valley, Los Angeles | Equinix, Digital Realty, CoreSite
Illinois    260    12 TWh    Chicago (Elk Grove Village) | Microsoft, Equinix, Digital Realty
Ohio    220    7 TWh    Columbus (New Albany) | Google, Meta, Amazon (AWS)
Arizona    180    10 TWh    Phoenix, Mesa | Apple, Microsoft, Vantage
Georgia    180    9 TWh    Atlanta area | Switch, Google, Microsoft
New York    150    4 TWh    NYC Metro, Buffalo | Equinix, DataBank
Oregon    150    6.5 TWh    Hillsboro, Prineville | Apple, Meta
Washington    140    4 TWh    Quincy, Seattle | Microsoft, Amazon (AWS)
Florida    130    4 TWh    Miami, Tampa | Equinix, Digital Realty
Iowa    110    3.5 TWh    Des Moines area | Apple, Google, Meta
North Carolina    110    4 TWh    Charlotte, Research Triangle | Apple, Google
Pennsylvania    105    2 TWh    Philadelphia, Pittsburgh
New Jersey    90    2 TWh    Secaucus (NYC Metro)
Indiana    80    1.5 TWh    Indianapolis
Minnesota    80    1.5 TWh    Minneapolis
Nevada    65    2.5 TWh    Las Vegas, Reno | Switch, Apple
Connecticut    65    1 TWh    Stamford, Hartford
Colorado    65    1.5 TWh    Denver
Tennessee    65    1.5 TWh    Nashville, Memphis
Michigan    60    1 TWh    Detroit, Grand Rapids
Missouri    50    1 TWh    St. Louis, Kansas City
Wisconsin    50    0.8 TWh    Milwaukee, Madison
Maryland    45    0.8 TWh    Baltimore
Utah    45    2.5 TWh    Salt Lake City (Bluffdale) | Meta, Google
Nebraska    40    2 TWh    Omaha | Google, Meta
Kentucky    40    0.6 TWh    Louisville
Oklahoma    40    0.6 TWh    Oklahoma City, Tulsa
South Carolina    35    0.5 TWh    Charleston, Greenville
Alabama    30    0.5 TWh    Birmingham, Huntsville
Montana    30    0.4 TWh    Billings
Louisiana    25    0.4 TWh    New Orleans
New Mexico    25    1.5 TWh    Albuquerque | Meta
North Dakota    25    0.4 TWh    Fargo
Delaware    20    0.3 TWh    Wilmington
Kansas    20    0.3 TWh    Wichita
Wyoming    20    0.6 TWh    Cheyenne | Microsoft
Idaho    15    0.2 TWh    Boise
New Hampshire    15    0.2 TWh    Manchester
Mississippi    15    0.2 TWh    Jackson
Hawaii    10    0.2 TWh    Honolulu
Maine    10    0.2 TWh    Portland
West Virginia    10    0.2 TWh    Charleston
Rhode Island    10    0.2 TWh    Providence
District of Columbia    10    0.2 TWh    Washington D.C.
Arkansas    10    0.2 TWh    Little Rock
South Dakota    10    0.2 TWh    Sioux Falls
Alaska    5    0.2 TWh    Anchorage
Vermont    5    0.2 TWh    Burlington
Massachusetts    55    1 TWh    Boston area, Holyoke
"""

#regex for power usage
pattern_pw = re.compile(r"""
    ^([A-Za-z .]+?)        # state name
    \s+([\d,]+|\d+\+?)     # number of datacenters
    \s+([\d.]+)\s*TWh      # power usage
""", re.VERBOSE | re.MULTILINE)

rows_pw = pattern_pw.findall(text_pw_us)
dc_pw_usage = np.array(rows_pw, dtype=object)

##2024 population data from https://www.statsamerica.org/sip/rank_list.aspx?rank_label=pop1
'''
was originally going to be used to examine a per capita data center power drain but seems more useful to look at
data center pwoer usage as a fraction of total state power draw
'''
text_pop = """
1	California	06000	39,431,263
2	Texas	48000	31,290,831
3	Florida	12000	23,372,215
4	New York	36000	19,867,248
5	Pennsylvania	42000	13,078,751
6	Illinois	17000	12,710,158
7	Ohio	39000	11,883,304
8	Georgia	13000	11,180,878
9	North Carolina	37000	11,046,024
10	Michigan	26000	10,140,459
11	New Jersey	34000	9,500,851
12	Virginia	51000	8,811,195
13	Washington	53000	7,958,180
14	Arizona	04000	7,582,384
15	Tennessee	47000	7,227,750
16	Massachusetts	25000	7,136,171
17	Indiana	18000	6,924,275
18	Maryland	24000	6,263,220
19	Missouri	29000	6,245,466
20	Wisconsin	55000	5,960,975
21	Colorado	08000	5,957,493
22	Minnesota	27000	5,793,151
23	South Carolina	45000	5,478,831
24	Alabama	01000	5,157,699
25	Louisiana	22000	4,597,740
26	Kentucky	21000	4,588,372
27	Oregon	41000	4,272,371
28	Oklahoma	40000	4,095,393
29	Connecticut	09000	3,675,069
30	Utah	49000	3,503,613
31	Nevada	32000	3,267,467
32	Iowa	19000	3,241,488
33	Arkansas	05000	3,088,354
34	Kansas	20000	2,970,606
35	Mississippi	28000	2,943,045
36	New Mexico	35000	2,130,256
37	Nebraska	31000	2,005,465
38	Idaho	16000	2,001,619
39	West Virginia	54000	1,769,979
40	Hawaii	15000	1,446,146
41	New Hampshire	33000	1,409,032
42	Maine	23000	1,405,012
43	Montana	30000	1,137,233
44	Rhode Island	44000	1,112,308
45	Delaware	10000	1,051,917
46	South Dakota	46000	924,669
47	North Dakota	38000	796,568
48	Alaska	02000	740,133
49	District of Columbia	11000	702,250
50	Vermont	50000	648,493
51	Wyoming	56000	587,618
"""

#regex for state pops
pattern_pop = re.compile(r"""
    \d+\s+                 # rank (ignored)
    ([A-Za-z ]+?)\s+       # state name
    \d{5}\s+               # FIPS (ignored)
    ([\d,]+)               # population
""", re.VERBOSE)

rows_pop = pattern_pop.findall(text_pop)
clean_rows_pop = [(state.strip(), int(pop.replace(",", ""))) for state, pop in rows_pop]
st_pop = np.array(clean_rows_pop, dtype=object)
df_pop=pd.DataFrame(st_pop,columns=['state','population'])

#merge population to power usage
df_dcpw=pd.DataFrame(dc_pw_usage,columns=['state','no. dc', 'pwr usage'])
df_dcpw=df_dcpw.merge(df_pop,left_on='state',right_on='state',how='left')
#datacenter power usage / capita converted to MWh from TWh
df_dcpw['pwr usage cap']=round(1e6 * df_dcpw['pwr usage'].astype(float)/df_dcpw['population'].astype(float), 2)


#merge power usage to prices dataframe, calculate fractional data center power usage
data=data.merge(df_dcpw,left_on='state',right_on='state',how='left')
#data center power fraction, converting TWh to GWh to get true fraction
data['pwr usage frac'] = round(1000* data['pwr usage'].astype(float)/data['total usage'].astype(float), 2)

###
###PLOTTING
###
#prep state geometries and merged data
us_states = gpd.read_file(
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
)
merged = us_states.merge(data, left_on="name", right_on="state", how="right")
continental = merged[~merged["name"].isin(["Alaska", "Hawaii"])]
alaska = merged[merged["name"] == "Alaska"].copy()
hawaii = merged[merged["name"] == "Hawaii"].copy()

alaska.geometry = alaska.scale(0.35, 0.43, origin='center')
alaska.geometry = alaska.translate(xoff=30, yoff=-25)

hawaii.geometry = hawaii.scale(1.5, 1.5, origin='center')
hawaii.geometry = hawaii.translate(xoff=60, yoff=-30)

exam_val='delta_res'

#prep colorbar
cmap = plt.cm.bwr
vmin = merged[exam_val].min()
vmax = merged[exam_val].max()
norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

fig, ax = plt.subplots(1, 1, figsize=(14, 8))

#continental us
continental.plot(
    column=exam_val,
    cmap=cmap,
    linewidth=0.8,
    edgecolor="0.8",
    legend=False,
    ax=ax
)

#ax.set_title(r"$\Delta_{Residential} - \Delta_{Industrial}$ (2024 $\rightarrow$ 2025) [¢/kWh]", fontsize=16)
ax.set_title(r"$\Delta_{Residential}$ (2024 $\rightarrow$ 2025) [¢/kWh]", fontsize=16)
ax.axis("off")

#alaska
ax_ak = fig.add_axes([0.06, 0.05, 0.2, 0.4])  # [left, bottom, width, height]
alaska.plot(
    column=exam_val,
    cmap=cmap,
    linewidth=0.8,
    edgecolor="0.8",
    legend=False,
    ax=ax_ak
)
ax_ak.axis("off")

#hawaii
ax_hi = fig.add_axes([0.27, 0.1, 0.10, 0.25])
hawaii.plot(
    column=exam_val,
    cmap=cmap,
    linewidth=0.8,
    edgecolor="0.8",
    legend=False,
    ax=ax_hi
)
ax_hi.axis("off")

### labels for DC power usage

value_column ='pwr usage'

# Plot continental labels
for idx, row in continental.iterrows():
    if row.geometry is None:
        continue
    x, y = row.geometry.centroid.coords[0]
    ax.text(
        x, y,
        f"{row[value_column]}",
        ha='center', va='center',
        fontsize=8, color='black',
        path_effects=[pe.withStroke(linewidth=1.5, foreground="white")]
    )

# Plot Alaska labels
for idx, row in alaska.iterrows():
    if row.geometry is None:
        continue
    x, y = row.geometry.centroid.coords[0]
    ax_ak.text(
        x, y,
        f"{row[value_column]}",
        ha='center', va='center',
        fontsize=7, color='black',
        path_effects=[pe.withStroke(linewidth=1.2, foreground="white")]
    )

# Plot Hawaii labels
for idx, row in hawaii.iterrows():
    if row.geometry is None:
        continue
    x, y = row.geometry.centroid.coords[0]
    ax_hi.text(
        x, y,
        f"{row[value_column]}",
        ha='center', va='center',
        fontsize=7, color='black',
        path_effects=[pe.withStroke(linewidth=1.2, foreground="white")])
###

#colorbar
cbar_ax = fig.add_axes([0.25, 0.08, 0.5, 0.035])  # [left, bottom, width, height]
sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
sm._A = []
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cbar.set_label('Favors Residential'+((' ')*(95))+'Favors Industrial', fontsize=12)
ax.text(-82,48,'#\'s = Data Center Power Usage [TWh]',fontsize=12)


#plt.savefig('figures/US_price_delta_v1.png',dpi=500)
plt.show()