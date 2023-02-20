# Seattle Places

Streamlit + Pocketbase app for tracking fun spots in Seattle

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://seattle.streamlit.app)

![Demo gif of map and selection](demo.gif)


## Fly.io Pocketbase setup

[reference](https://github.com/pocketbase/pocketbase/discussions/537)

Run Stack: `docker-compose up --build`

### Overview of `./backend`

- `Dockerfile`
  - builds the application in a container to be run by Fly
  - Uses alpine image so we can have shell access for putting data into the application if needed (could use a distroless image if no need for uploading a database)

### Backend Local

#### Init

``` sh
mkdir backend
cd backend
touch Dockerfile main.go
# setup minimal pocketbase
go mod init
go mod tidy
# go get github.com/pocketbase/pocketbase
```

#### Run with Go

From `./backend`:

```sh
go run main.go serve --http=localhost:8080
```

#### Fly CTL

Follow the installation instructions from [https://fly.io/docs/hands-on/install-flyctl/]():

```sh
curl -L https://fly.io/install.sh | sh

flyctl auth signup

fly auth login
```

##### Fly Deploy

```sh
cd backend
fly launch
# fly.toml created
flyctl volumes create pb_data --size=1
```

Add the following `[mounts]` section in `fly.toml` just below the top entries:

```toml file:fly.toml
app = "YOUR_APP_NAME"
kill_signal = "SIGINT"
kill_timeout = 5
processes = []

[mounts]
  destination = "/bin/pb_data"
  source = "pb_data"
```

Deploy as needed

```sh
# from ./backend
fly deploy
```

Check logs as needed

```sh
fly logs -a seattleplaces
```

Replace database as needed from local file

```sh
flyctl ssh sftp shell -a seattleplaces
>> put new.data.db /bin/pb_data/new.data.db
# ^c
fly ssh console -a seattleplaces
/ mv /bin/pb_data/new.data.db /bin/pb_data/data.db
# ^d
flyctl apps restart seattleplaces
```
