from ubuntu

run apt-get -y update && apt-get -y install python-dev python-pip libffi-dev 

run apt-get -y install libssl-dev

add . /jrpc

workdir /jrpc

run python setup.py install

workdir /jrpc/examples

entrypoint ["twistd", "-noy"]
cmd ["math/math.tac"]
