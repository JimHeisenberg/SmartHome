# develop environment:
# caddy 2.5.0
# bootstrap 4.3.1
# mysql 8.0.28
# Flask==2.0.0
# itsdangerous==2.0.0
# PyMySQL==1.0.2
# requests==2.22.0

# install:
# apt install mysql-server
# python3 -m pip install -r requirements.txt

# run
nohup python ./server/server.py 2>&1 &
# ps -aux | grep python
# caddy start | stop | reload | --watch