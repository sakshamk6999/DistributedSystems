FROM python:3.11.14-alpine3.22
WORKDIR /app
COPY . .
EXPOSE 50000
CMD ["python3", "-u", "Backend/BuyerServer.py"]
