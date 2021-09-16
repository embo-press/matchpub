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
RUN pip install python-dotenv
RUN pip install IMAPClient==2.2.0
RUN pip install notebook==6.2.0

ARG user_id
ARG group_id
# RUN useradd --uid $user_id --gid $group_id matchpub
# USER matchpub
WORKDIR /app
CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]