FROM python:3

WORKDIR /app
EXPOSE 80
EXPOSE 443
EXPOSE 25565

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-m", "ServerStart" ]
