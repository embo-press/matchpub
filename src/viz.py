from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
import plotly.express as px
from .utils import ed_rej_matcher, post_review_rej_matcher, accept_matcher


# import matplotlib.pyplot as plt
# matplotlib.use('TkAgg')  # supported values are ['GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg', 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 'TkAgg', 'TkCairo', 'WebAgg', 'WX', 'WXAgg', 'WXCairo', 'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template']#

# aggrnyl     agsunset    blackbody   bluered     blues       blugrn      bluyl       brwnyl
# bugn        bupu        burg        burgyl      cividis     darkmint    electric    emrld
# gnbu        greens      greys       hot         inferno     jet         magenta     magma
# mint        orrd        oranges     oryel       peach       pinkyl      plasma      plotly3
# pubu        pubugn      purd        purp        purples     purpor      rainbow     rdbu
# rdpu        redor       reds        sunset      sunsetdark  teal        tealgrn     turbo
# viridis     ylgn        ylgnbu      ylorbr      ylorrd      algae       amp         deep
# dense       gray        haline      ice         matter      solar       speed       tempo
# thermal     turbid      armyrose    brbg        earth       fall        geyser      prgn
# piyg        picnic      portland    puor        rdgy        rdylbu      rdylgn      spectral
# tealrose    temps       tropic      balance     curl        delta       oxy         edge
# hsv         icefire     phase       twilight    mrybm       mygbm

# aliceblue, antiquewhite, aqua, aquamarine, azure,
# beige, bisque, black, blanchedalmond, blue,
# blueviolet, brown, burlywood, cadetblue,
# chartreuse, chocolate, coral, cornflowerblue,
# cornsilk, crimson, cyan, darkblue, darkcyan,
# darkgoldenrod, darkgray, darkgrey, darkgreen,
# darkkhaki, darkmagenta, darkolivegreen, darkorange,
# darkorchid, darkred, darksalmon, darkseagreen,
# darkslateblue, darkslategray, darkslategrey,
# darkturquoise, darkviolet, deeppink, deepskyblue,
# dimgray, dimgrey, dodgerblue, firebrick,
# floralwhite, forestgreen, fuchsia, gainsboro,
# ghostwhite, gold, goldenrod, gray, grey, green,
# greenyellow, honeydew, hotpink, indianred, indigo,
# ivory, khaki, lavender, lavenderblush, lawngreen,
# lemonchiffon, lightblue, lightcoral, lightcyan,
# lightgoldenrodyellow, lightgray, lightgrey,
# lightgreen, lightpink, lightsalmon, lightseagreen,
# lightskyblue, lightslategray, lightslategrey,
# lightsteelblue, lightyellow, lime, limegreen,
# linen, magenta, maroon, mediumaquamarine,
# mediumblue, mediumorchid, mediumpurple,
# mediumseagreen, mediumslateblue, mediumspringgreen,
# mediumturquoise, mediumvioletred, midnightblue,
# mintcream, mistyrose, moccasin, navajowhite, navy,
# oldlace, olive, olivedrab, orange, orangered,
# orchid, palegoldenrod, palegreen, paleturquoise,
# palevioletred, papayawhip, peachpuff, peru, pink,
# plum, powderblue, purple, red, rosybrown,
# royalblue, rebeccapurple, saddlebrown, salmon,
# sandybrown, seagreen, seashell, sienna, silver,
# skyblue, slateblue, slategray, slategrey, snow,
# springgreen, steelblue, tan, teal, thistle, tomato,
# turquoise, violet, wheat, white, whitesmoke,
# yellow, yellowgreen

def normalize_decision(analysis: pd.DataFrame):
    rejected_ed = analysis['decision'].apply(lambda x: ed_rej_matcher.match(x) is not None)
    rejected_post = analysis['decision'].apply(lambda x: post_review_rej_matcher.match(x) is not None)
    accepted = analysis['decision'].apply(lambda x: accept_matcher.match(x) is not None)
    analysis.loc[rejected_ed, 'decision'] = 'rejected before review'
    analysis.loc[rejected_post, 'decision'] = 'rejected after review'
    analysis.loc[accepted, 'decision'] = 'accepted'


def citation_distribution(analysis: pd.DataFrame, dest_path: str):
    dest_path = Path(dest_path)
    normalize_decision(analysis)
    fig = px.violin(
        analysis,
        y="citations",
        x="decision",
        category_orders={"decision": ['accepted', 'rejected before review', 'rejected after review']},
        color_discrete_sequence=px.colors.qualitative.G10,
        # color_discrete_map = {"accepted": "aliceblue", "rejected before review": "red", 'rejected after review': "orange"},
        points="all",
        title="Citation distribution by decision type",
        color="decision",
        template="seaborn",
    )
    # https://plotly.com/python/styling-plotly-express/
    save_fig(fig, 'cite_distro', dest_path)


def overview(found: pd.DataFrame, not_found, dest_path: str):
    normalize_decision(found)
    normalize_decision(not_found)
    found['status'] = 'retrieved from PMC'
    not_found['status'] = 'not retrieved from PMC'
    overview = pd.concat([found, not_found])
    overview['count'] = 1
    overview['name'] = 'Overview'
    fig1 = px.treemap(
        overview,
        path=['name', 'status', 'decision'],
        values='count',
        color='status',
        # color_discrete_sequence=px.colors.qualitative.G10,
        color_discrete_map={'(?)': 'steelblue', 'retrieved from PMC': 'forestgreen', 'not retrieved from PMC': 'red'}
    )
    fig1.update_traces(
        textinfo='label+percent parent+value',
        textfont=dict(
            family="arial",
            color="white"
        )
    )
    fig1.update_layout(
        title="Analysis overview",
        title_font_size=14,
    )
    save_fig(fig1, 'analysis_overview', dest_path)


def journal_distributions(analysis: pd.DataFrame, dest_path: str, max_slices: int = 21):
    normalize_decision(analysis)
    max_slices = max_slices if len(analysis) > max_slices else len(analysis)
    analysis['count'] = 1  # adding a column to count
    all_rejections = analysis[(analysis.decision == 'rejected before review') | (analysis.decision == 'rejected after review')]
    grouped = all_rejections.groupby("journal").count()  # journal becomes the index
    df = pd.DataFrame(grouped.reset_index())  # reset_index() will insert back column journal!
    df.sort_values(by='count', ascending=False, inplace=True)
    df.reset_index(inplace=True)  # so that loc[] below works as expected
    df.loc[max_slices - 1:, 'journal'] = 'other'
    fig1 = px.pie(
        df,
        values='count',  # maybe simpler to take analysis and use values='journal'
        names='journal',
        # width=600, height=600,
        color='journal',
        # color_discrete_sequence=px.colors.sequential.Viridis,
        color_discrete_sequence=px.colors.qualitative.Prism
        # color_discrete_sequence=px.colors.sequential.Aggrnyl
    )
    fig1.update_traces(
        textposition='outside',
        textinfo='label',
        textfont_size=8,
        marker=dict(
            line=dict(
                width=0.5,
                color='White'
            )
        )
    )
    fig1.update_layout(
        title='Fate of rejected manuscripts',
        title_font_size=14,
        showlegend=False,
        # uniformtext_minsize=8, uniformtext_mode='hide',
        # legend=dict(
        #     yanchor="top",
        #     y=0,
        #     xanchor="right",
        #     x=0,
        #     font=dict(
        #         family="Arial",
        #         size=5,
        #         color="black"
        #     )
        # )
    )
    save_fig(fig1, 'journal_distro_pie', dest_path)
    fig2 = px.treemap(
        analysis,
        path=['decision', 'journal'],
        values='count',
        color='journal',
        color_discrete_sequence=px.colors.qualitative.Antique,
    )
    fig2.update_traces(
        marker=dict(
            line=dict(
                width=1,
                color='White'
            )
        )
    )
    fig2.update_layout(
        title='Fate of manuscripts by decision type.',
        title_font_size=14,
    )
    save_fig(fig2, 'journal_distro_tree', dest_path)


def save_fig(fig, name: str, dest_path: str):
    dest_path = Path(dest_path)
    path = Path('/plots') / f"{dest_path.stem}-{name}.pdf"
    fig.write_image(str(path))


def self_test():
    found = pd.read_excel('/results/test_results.xlsx', header=0)
    citation_distribution(found, '/test_cite_distro')
    journal_distributions(found, '/test_jou_distro')


if __name__ == "__main__":
    parser = ArgumentParser(description="Visualizations for matchpub results.")
    parser.add_argument("input", nargs="?", help="Path to the input Excel file.")
    args = parser.parse_args()
    input_path = args.input
    not_found_path = input_path.replace("found", "not_found")
    if input_path:
        found = pd.read_excel(input_path)
        not_found = pd.read_excel(not_found_path)
        citation_distribution(found, input_path)
        journal_distributions(found, input_path)
        overview(found, not_found, input_path)
    else:
        self_test()
