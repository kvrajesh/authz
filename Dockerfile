FROM python:3.3
RUN pip install py2neo==3.0
RUN mkdir ../app
RUN cp -r * ../app
COPY 
WORKDIR /app
CMD ["python", "authz.py"]