FROM python:3.9-slim-buster

RUN python -m pip install --upgrade setuptools pip wheel
RUN python -m pip install --upgrade pyyaml
RUN python -m pip install syncer
RUN python -m pip install Firefly-III-API-Client
RUN python -m pip install python-binance
RUN python -m pip install cryptocom-exchange
RUN python -m pip install aiohttp

RUN mkdir /opt/crypto-trades-firefly-iii
COPY ./ /opt/crypto-trades-firefly-iii/

CMD cd /opt/crypto-trades-firefly-iii && python src/main.py
