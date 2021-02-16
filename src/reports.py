from pathlib import Path
from argparse import ArgumentParser

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
# import plotly.graph_objects as go

from . import logger, REPORTS

# import matplotlib.pyplot as plt
# matplotlib.use('TkAgg')  # supported values are ['GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg', 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 'TkAgg', 'TkCairo', 'WebAgg', 'WX', 'WXAgg', 'WXCairo', 'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template']#


class MatchPubReport:
    def __init__(self, found: pd.DataFrame, not_found: pd.DataFrame, dest_path: str, report_dir: str = REPORTS, name='generic'):
        self.found = found
        self.not_found = not_found
        self.basename = Path(dest_path).stem
        self.name = name
        self.report_dir = Path(report_dir)
        self.path = None
        report = self.generate_report()
        self.save_report(report)

    def generate_report(self) -> Figure:
        NotImplementedError

    def save_report(self, fig: Figure):
        if fig is not None:
            self.path = self.report_dir / f"{self.basename}-{self.name}.pdf"
            fig.write_image(str(self.path))
            logger.info(f"saved report {self.path}")


class Overview(MatchPubReport):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, name='analysis_overview')

    def generate_report(self) -> Figure:
        self.found['status'] = 'retrieved from PMC'
        self.not_found['status'] = 'not retrieved from PMC'
        overview = pd.concat([self.found, self.not_found])
        overview['count'] = 1
        overview['name'] = 'Overview'
        fig = px.treemap(
            overview,
            path=['name', 'status', 'decision'],
            values='count',
            color='status',
            color_discrete_map={'(?)': 'steelblue', 'retrieved from PMC': 'forestgreen', 'not retrieved from PMC': 'red'}
        )
        fig.update_traces(
            textinfo='label+percent parent+value',
            textfont=dict(
                family="arial",
                color="white"
            )
        )
        fig.add_annotation(
            text=f"{len(self.found)} articles found from {len(overview)} total submissions",
            xref="paper", yref="paper", xanchor='left', yanchor='top',
            x=0, y=0,
            showarrow=False,
        )
        fig.update_layout(
            title="Analysis overview",
            title_font_size=14,
        )
        return fig


class CitationDistribution(MatchPubReport):

    def __init__(self, found, *args, **kwargs):
        super().__init__(found, None, *args, **kwargs, name='citation_distribution')

    def generate_report(self) -> Figure:
        fig = px.violin(
            self.found,
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
        return fig


class JournalDistributionAllRejects(MatchPubReport):
    def __init__(self, found, *args, **kwargs):
        super().__init__(found, None, *args, **kwargs)

    def all_rejects(self) -> pd.DataFrame:
        self.found['count'] = 1  # adding a column to count
        all_rejections = self.found[(self.found.decision == 'rejected before review') | (self.found.decision == 'rejected after review')]
        return all_rejections


class JournalDistributionPie(JournalDistributionAllRejects):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, name='journal_distribution_pie')

    def generate_report(self, max_slices: int = 21):
        max_slices = max_slices if len(self.found) > max_slices else len(self.found)
        all_rejections = self.all_rejects()
        grouped = all_rejections[['journal', 'count']].groupby("journal").count()  # journal becomes the index
        df = pd.DataFrame(grouped.reset_index())  # reset_index() will insert back column journal!
        df.sort_values(by='count', ascending=False, inplace=True)  # to dispaly nice and to cut at maximum slices
        df.reset_index(inplace=True)  # so that index follows new sorting order and loc[] below works as expected
        df.loc[max_slices - 1:, 'journal'] = 'other'
        fig = px.pie(
            df,
            values='count',
            names='journal',
            # width=600, height=600,
            color='journal',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig.update_traces(
            textposition='outside',
            textinfo='label+value',
            textfont_size=8,
            marker=dict(
                line=dict(
                    width=0.5,
                    color='White'
                )
            )
        )
        fig.update_layout(
            title='Fate of rejected manuscripts',
            title_font_size=14,
            showlegend=False,
        )
        return fig


class JournalDistributionTreeMap(JournalDistributionAllRejects):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, name='journal_distribution_tree_map')

    def generate_report(self):
        all_rejects = self.all_rejects()
        fig = None
        if len(all_rejects) > 0:
            fig = px.treemap(
                all_rejects,
                path=['decision', 'journal'],
                values='count',
                color='journal',
                color_discrete_sequence=px.colors.qualitative.Antique,
            )
            fig.update_traces(
                marker=dict(
                    line=dict(
                        width=1,
                        color='White'
                    )
                )
            )
            fig.update_layout(
                title='Fate of manuscripts by decision type.',
                title_font_size=14,
            )
        else:
            logger.info(f"no tree map for all rejections (len {len(all_rejects)})")
        return fig


class TimeToPublish(MatchPubReport):

    def __init__(self, found, *args, **kwargs):
        super().__init__(found, None, *args, **kwargs, name='time_to_publish')

    def generate_report(self):
        self.found['pub_date'] = self.found['pub_date'].astype('datetime64[ns]')
        self.found['time_to_publish'] = self.found['pub_date'] - self.found['sub_date']
        self.found['time_to_publish'] = self.found['time_to_publish'].dt.days
        self.found.loc[self.found['time_to_publish'] < 0, 'time_to_publish'] = None
        fig = px.violin(
            self.found,
            y="time_to_publish",
            x="decision",
            category_orders={"decision": ['accepted', 'rejected before review', 'rejected after review']},
            color_discrete_sequence=px.colors.qualitative.G10,
            points="all",
            title="Distribution of the time to publish by decision type",
            color="decision",
            template="seaborn",
        )
        return fig


class PreprintOverview(MatchPubReport):

    def __init__(self, found, *args, **kwargs):
        super().__init__(found, None, *args, **kwargs, name='preprint_overview')

    def generate_report(self):
        preprints = self.found[self.found.is_preprint].copy()
        preprints["count"] = 1
        preprints["published"] = "not yet published"
        preprints.loc[preprints["preprint_published_doi"].notnull(), "published"] = "published"
        fig = None
        if len(preprints) > 0:
            fig = px.treemap(
                preprints,
                path=["published", "decision"],
                values="count",
                color="decision",
                # color_discrete_sequence=px.colors.qualitative.G10,
                color_discrete_map={
                    "(?)": "brown",
                    "accepted": "red",
                    "rejected before review": "grey",
                    "rejected after review": "grey"
                }
            )
            fig.update_layout(
                title="Publication status of preprints matching the journal submissions.",
                title_font_size=14
            )
            fig.update_traces(
                marker={
                    "line": {
                        "width": 1,
                        "color": "White"
                    }
                }
            )
        else:
            logger.info("no preprints!")
        return fig


class UnlinkedPreprints(MatchPubReport):

    def __init__(self, found, *args, **kwargs):
        super().__init__(found, None, *args, **kwargs, name='unlinked_preprints')

    def generate_report(self):
        accepted = self.found[self.found['decision'] == 'accepted'].copy()
        accepted["preprint_published"] = False
        accepted.loc[accepted["preprint_published_doi"].notnull(), "preprint_published"] = True
        accepted["warning"] = "OK"
        accepted.loc[(accepted.is_preprint) & (~accepted.preprint_published), ["warning"]] = "UNLINKED?"
        cols = [
            "manuscript_nm",
            "journal",
            "doi",
            "retrieved_title",
            "original_title",
            "decision",
            "retrieved_abstract",
            "preprint_published",
            "preprint_published_doi",
            "warning"
        ]
        accepted.sort_values(by='original_title', ascending=False, inplace=True)
        return accepted[cols]

    def save_report(self, report: pd.DataFrame) -> str:
        self.path = self.report_dir / f"{self.basename}-unlinked_preprints.xlsx"
        with pd.ExcelWriter(self.path) as writer:
            report.to_excel(writer)


def self_test():
    found = pd.read_excel('/results/test_results.xlsx', header=0)
    CitationDistribution(found, '/test_cite_distro')
    JournalDistributionTreeMap(found, '/test_jou_distro')


if __name__ == "__main__":
    parser = ArgumentParser(description="Visualizations for matchpub results.")
    parser.add_argument("input", nargs="?", help="Path to the input Excel file.")
    args = parser.parse_args()
    input_path = args.input
    not_found_path = input_path.replace("found", "not_found")
    print(f"Loading {input_path} and {not_found_path}")
    if input_path:
        found = pd.read_excel(input_path)
        not_found = pd.read_excel(not_found_path)
        PreprintOverview(found, input_path)
        UnlinkedPreprints(found, input_path)
        CitationDistribution(found, input_path)
        JournalDistributionTreeMap(found, input_path)
        Overview(found, not_found, input_path)
        TimeToPublish(found, input_path)
    else:
        self_test()


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
