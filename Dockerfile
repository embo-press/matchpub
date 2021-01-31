FROM python:3.7-buster

RUN apt-get update \
&& pip install --upgrade pip setuptools
RUN pip install spacy
# need to download language model which is large: 782.7 MB
RUN python -m spacy download en_core_web_lg
RUN pip install numpy
RUN pip install nltk
RUN pip install requests
RUN pip install unidecode
RUN pip install lxml
RUN pip install pandas
RUN pip install openpyxl
RUN pip install xlrd
RUN pip install tqdm
RUN pip install beautifulsoup4
RUN pip install plotly
RUN pip install matplotlib
RUN pip install kaleido

ARG user_id
ARG group_id
USER $user_id:$dgroup_id
