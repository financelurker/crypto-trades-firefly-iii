FROM python:3.9-slim-buster

RUN python -m pip install --upgrade setuptools pip wheel
RUN python -m pip install --upgrade pyyaml
RUN python -m pip install Firefly-III-API-Client
RUN python -m pip install python-binance
RUN python -m pip install cryptocom-exchange

RUN mkdir /opt/crypto-trades-firefly-iii
COPY src/ /opt/src/

CMD cd /opt/crypto-trades-firefly-iii && python /src/main.py
