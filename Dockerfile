
FROM python:3.7

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
EXPOSE 8000

WORKDIR /project_x


# Installing numpy, scipy, psycopg2, gensim
RUN python3 -m pip install --upgrade pip
RUN pip3 install pandas --no-cache-dir --disable-pip-version-check
RUN pip install celery==5.2.3
#Install dependencies
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .