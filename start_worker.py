import os
from redis import Redis
from rq import Queue, Connection, Worker

redis_host = "redis-15044.c278.us-east-1-4.ec2.cloud.redislabs.com"
redis_port = 15044
redis_password = "sPSPqmznaof65h2ltypLo9Bn1U29oLs1"



redis_conn = Redis(redis_host, redis_port, password = redis_password)
generate_playlist_queue = Queue(connection=redis_conn) 





if __name__ == '__main__':
    print("running worker")
    with Connection(redis_conn):
        worker = Worker(generate_playlist_queue)
        worker.work()