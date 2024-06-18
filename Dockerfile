FROM continuumio/miniconda3

WORKDIR /app

COPY requirements.txt /app/

RUN conda install -c conda-forge --file /app/requirements.txt

COPY . .

CMD ["python", "app.py"]

EXPOSE 8501