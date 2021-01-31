import re
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
import plotly.express as px


# import matplotlib.pyplot as plt
# matplotlib.use('TkAgg')  # supported values are ['GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg', 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 'TkAgg', 'TkCairo', 'WebAgg', 'WX', 'WXAgg', 'WXCairo', 'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template']#


def citation_distribution(analysis: pd.DataFrame, dest_path: str):
    dest_path = Path(dest_path)
    rejected_ed = analysis['decision'].apply(lambda x: re.match(r".*reject post", x, re.IGNORECASE) is None)
    rejected_post = analysis['decision'].apply(lambda x: re.match(r".*reject post", x, re.IGNORECASE) is not None)
    accepted = analysis['decision'].apply(lambda x: re.match(r".*accept", x, re.IGNORECASE) is not None)
    analysis.loc[rejected_ed, 'decision'] = 'rejected before review'
    analysis.loc[rejected_post, 'decision'] = 'rejected after review'
    analysis.loc[accepted, 'decision'] = 'accepted'
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


def journal_distributions(analysis: pd.DataFrame, dest_path: str):
    dest_path = Path(dest_path)
    analysis['count'] = 1  # adding a column to count
    # analysis['journal_abbr'] = analysis['journal'].apply(
    #     lambda name: 
    #         ".".join([n[0].upper() for n in name.split(" ") if n.isalpha() and len(n) > 3]) if len(name) > 30 else name
    # )
    rejected = analysis[analysis['decision'].apply(lambda x: re.search(r"reject", x, re.IGNORECASE) is not None)]
    grouped = rejected.groupby("journal").count()  # journal becomes the index
    df = pd.DataFrame(grouped.reset_index())  # reset_index() will insert back column journal!
    df.loc[df["count"] < 10, 'journal'] = 'other'
    fig1 = px.pie(
        df,
        values='count',
        names='journal',
        width=600, height=600,
        color='journal',
        color_discrete_sequence=px.colors.qualitative.G10,
        # color_discrete_sequence=px.colors.sequential.Aggrnyl
    )
    fig1.update_traces(
        textposition='outside',
        textinfo='label',
        textfont_size=5,

    )
    fig1.update_layout(
        title='Fate of rejected manuscripts',
        title_font_size=12,
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
        title='Fate of manuscripts by decision type.',
    )
    save_fig(fig2, 'journal_distro_tree', dest_path)


def save_fig(fig, name: str, dest_path: str):
    path = Path('/plots') / f"{dest_path.stem}-{name}.pdf"
    fig.write_image(str(path))

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


def self_test():
    analysis = pd.read_excel('/results/test_results.xlsx', header=0)
    citation_distribution(analysis, '/test_cite_distro')
    journal_distributions(analysis, '/test_jou_distro')


if __name__ == "__main__":
    parser = ArgumentParser(description="Visualizations for matchpub results.")
    parser.add_argument("input", nargs="?", help="Path to the input Excel file.")
    args = parser.parse_args()
    input_path = args.input
    if input_path:
        analysis = pd.read_excel(input_path)
        citation_distribution(analysis, input_path)
        journal_distributions(analysis, input_path)
    self_test()
