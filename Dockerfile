FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL/GEOS library paths for GeoDjango runtime
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so.1

WORKDIR /app

COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["sh", "-c", "python Satellitor/manage.py migrate && python Satellitor/create_superuser.py && python Satellitor/manage.py runserver 0.0.0.0:8000"]



