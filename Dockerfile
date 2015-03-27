from ubuntu

run apt-get -y update && apt-get -y install python-dev python-pip libffi-dev libssl-dev

add requirements.txt /requirements.txt

run pip install -r /requirements.txt

add . /jrpc

run cd /jrpc && python setup.py install

workdir /jrpc/examples

entrypoint ["twistd", "-noy"]
cmd ["math/math.tac"]
