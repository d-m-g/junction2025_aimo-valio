##############
# Build step #
##############
FROM gradle:8.10.2-jdk21 AS order_builder

WORKDIR /workspace/order_fulfilment_service
COPY order_fulfilment_service/ ./

RUN chmod +x gradlew && \
    ./gradlew --no-daemon clean bootJar

RUN JAR_PATH=$(ls build/libs | grep -E '\.jar$' | grep -v plain | head -n 1) && \
    cp "build/libs/${JAR_PATH}" /tmp/order_fulfilment_service.jar

###############
# Runtime env #
###############
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      ca-certificates \
      curl \
      libpq-dev \
      openjdk-21-jre-headless \
      postgresql \
      postgresql-client \
      postgresql-contrib \
      procps \
      tini \
      util-linux \
  && rm -rf /var/lib/apt/lists/*

# Allow remote Postgres connections (exposed via Docker)
RUN PG_MAJOR=$(ls /etc/postgresql | head -n 1) && \
    sed -ri "s/#?listen_addresses\s*=\s*'[^']*'/listen_addresses = '*'/g" /etc/postgresql/${PG_MAJOR}/main/postgresql.conf && \
    echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/${PG_MAJOR}/main/pg_hba.conf && \
    echo "host all all ::/0 md5" >> /etc/postgresql/${PG_MAJOR}/main/pg_hba.conf

COPY requirements.txt requirements.txt
COPY stock_prediction/requirements.txt stock_prediction/requirements.txt
COPY NLU/requirements.txt NLU/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r stock_prediction/requirements.txt \
    && pip install --no-cache-dir -r NLU/requirements.txt

COPY services ./services
COPY stock_prediction ./stock_prediction
COPY NLU ./NLU
COPY warehouse-db ./warehouse-db
COPY Data ./Data
COPY Docs ./Docs
COPY analysis ./analysis
COPY training ./training
COPY models ./models

COPY --from=order_builder /tmp/order_fulfilment_service.jar /opt/order/order_fulfilment_service.jar
COPY start-all.sh /app/start-all.sh
RUN chmod +x /app/start-all.sh

EXPOSE 8080 8000 8100 6060 5432

ENV WAREHOUSE_DB_HOST=localhost \
    WAREHOUSE_DB_PORT=5432 \
    WAREHOUSE_DB_NAME=warehouse \
    WAREHOUSE_DB_USER=warehouse_user \
    WAREHOUSE_DB_PASSWORD=warehouse_pass \
    SPRING_DATASOURCE_URL="jdbc:postgresql://localhost:5432/warehouse" \
    SPRING_DATASOURCE_USERNAME=warehouse_user \
    SPRING_DATASOURCE_PASSWORD=warehouse_pass \
    PREDICT_ORDER_URL="http://localhost:8100/predict/order" \
    SUBSTITUTION_SERVICE_URL="http://localhost:8000/substitution/suggest" \
    SHORTAGE_SERVICE_URL="http://localhost:8080/api/orders/shortage/proactive-call" \
    NLU_HOST=0.0.0.0 \
    NLU_PORT=6060 \
    SUBSTITUTION_PORT=8000 \
    STOCK_PREDICTION_PORT=8100 \
    ORDER_SERVICE_PORT=8080

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start-all.sh"]
