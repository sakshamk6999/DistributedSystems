The application consists of 2 TCP servers for the Buyer and the Seller use cases. The server handles multiple clients through spawning multiple threads for each client. The TCP clients provide an interactive CLI for the user. 

The storage is managed by MySQL, through the PyMySQL library in Python. Docker is used to manage the database deployment. With the compose.yaml file used to deploy both DBs at once.

This assignment runs on a single host. The Backend folder consists the Buyer and Seller servers and the Frontend folder consisting of the CLI clients.

