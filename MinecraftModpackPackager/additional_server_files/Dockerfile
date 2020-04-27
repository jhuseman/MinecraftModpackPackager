FROM openjdk:8u252-jre-slim-buster
COPY --from=python:3.8-slim-buster / /

WORKDIR /app
EXPOSE 80
EXPOSE 443
EXPOSE 25565

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-m", "ServerStartDocker" ]
