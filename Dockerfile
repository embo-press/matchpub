FROM python:3.7-slim

RUN apt-get update \
&& pip install --upgrade pip setuptools
RUN pip install nltk
RUN pip install spacy
RUN pip install requests
RUN pip install unidecode
RUN pip install lxml
RUN pip install numpy
RUN pip install pandas
RUN pip install openpyxl
RUN pip install xlrd
RUN pip install tqdm
RUN pip install beautifulsoup4
RUN python -m spacy download en_core_web_lg

ARG user_id
ARG group_id
USER $user_id:$dgroup_id
