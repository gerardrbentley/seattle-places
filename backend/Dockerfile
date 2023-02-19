FROM golang:1.19.3-buster AS build

WORKDIR /src/custom_pocketbase/

COPY go.mod .
COPY go.sum .

RUN go mod download

COPY . /src/custom_pocketbase/
RUN CGO_ENABLED=0 GO111MODULE=on GOOS=linux go build -o /bin/custom_pocketbase && \
    chmod 111 /bin/custom_pocketbase

FROM alpine:3.17 as final
COPY --from=build /bin/custom_pocketbase /bin/custom_pocketbase

CMD ["/bin/custom_pocketbase", "serve", "--http=0.0.0.0:8080"]
