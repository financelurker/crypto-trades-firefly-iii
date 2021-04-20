FROM python:3.9-slim-buster

RUN python -m pip install --upgrade setuptools pip wheel
RUN python -m pip install --upgrade pyyaml
RUN python -m pip install Firefly-III-API-Client
RUN python -m pip install python-binance
RUN python -m pip install cryptocom-exchange

RUN mkdir /opt/crypto-trades-firefly-iii
RUN mkdir /opt/crypto-trades-firefly-iii/exchanges
RUN mkdir /opt/crypto-trades-firefly-iii/firefly
RUN mkdir /opt/crypto-trades-firefly-iii/importer
RUN mkdir /opt/crypto-trades-firefly-iii/model
COPY src/firefly/firefly_wrapper.py /opt/crypto-trades-firefly-iii/firefly/
COPY src/exchanges/binance_wrapper.py /opt/crypto-trades-firefly-iii/exchanges/
COPY src/exchanges/cryptocom_wrapper.py /opt/crypto-trades-firefly-iii/exchanges/
COPY src/exchanges/exchange_interface.py /opt/crypto-trades-firefly-iii/exchanges/
COPY src/exchanges/exchange_interface_factory.py /opt/crypto-trades-firefly-iii/exchanges/
COPY src/importer/sync_timer.py /opt/crypto-trades-firefly-iii/importer/
COPY src/importer/sync_logic.py /opt/crypto-trades-firefly-iii/importer/
COPY src/model/transaction.py /opt/crypto-trades-firefly-iii/model/
COPY src/config.py /opt/crypto-trades-firefly-iii/
COPY src/migrate_firefly_identifiers.py /opt/crypto-trades-firefly-iii/
COPY src/main.py /opt/crypto-trades-firefly-iii/
COPY README.md /opt/crypto-trades-firefly-iii/

CMD python /opt/crypto-trades-firefly-iii/main.py
