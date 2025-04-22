FROM ubuntu:18.04
USER root
RUN apt-get update && apt-get install -y curl wget sudo python
ADD . /app
WORKDIR /app
RUN chmod 777 /app
RUN echo 'root:root' | chpasswd
RUN pip install --upgrade pip
RUN pip install flask
EXPOSE 80
CMD ["python", "app.py"]
