# HB DTA

## Objective

The objective is to write a *Facebook Messenger bot*, in *Python*, which reads a name or an `account_id` of a **Dota** player, and answer some statistics.

## Facebook Messenger

I've never used this API. I'm more familiar with *Slack*, but my experience with this chat platform is mostly unidirectional: **outputs only**; but also the need was different. So let's tackle this technology!

Messenger bot is quite easy to use:
- If someone writes to the bot, a HTTP request is sent to an endpoint (Webhook), so we'll have to be able to receive them
- The bot can write to Messenger by sending an HTTP request to their endpoint
- There is an authentification method, by exchanging a token (first time only)

## Dota API

The exercise was recommending to use [dota2api](http://dota2api.readthedocs.io/en/latest/index.html) Python Package, but I had some issues to generate API keys. So I Googled it, and found a great alternative: [OpenDota](https://docs.opendota.com/), which is, according to the docs, working exactly like the first one, it's simply a REST API, so we have to write the interface. `requests` seems a good candidate, as we'll also have to use it to write to Messenger.

## Choice of the Backend

Webhook / Webserver / HTTP pushes / HTTP requests, don't require a statefull system, so any webserver technology could work. Let's restrict to Python, the following technologies could work:

- Django
- Tornado
- Flack

I've already used *Django* a lot, so that would be the simplicity, however for performance, and asynchronous tasks, *Tornado* is way better.

But then comes the question of the infrastructure... And we also have 3* solutions:

- Standalone server (EC2, GCE)
- Apps Engine (GAE)
- Container Engine (ECS, GKE)

That's heavy! As we don't have a lot of time, let's consider another alternative: **AWS Lambda + API Gateway** (we cannot use the Google equivalent, as it's only working with Node). And we chose that solution for the following reasons:

- Stateless Webserver: can receive GET / POST requests easily
- Works with Python (2.7)
- A Lambda is a function, so by *invoking* Lambdas from other Lambdas, we can unlock super easily asynchronous (advantage taken from Tornado)
- Serverless: no infrastructure to maintain
- Nice feature I discovered later: **OpenDota** is blocking requests if there is a request rate lower that 1 / sec: as each Lambda has its own IP, no need to worry about that!
- (super) cheap

**I think we have our stack: AWS Lambda + API Gateway + Python2.7**

## Chat process

Before coding, let's analyse what we'll have to develop

![flow](https://www.dropbox.com/s/iypbrdn87o7jszj/Screenshot%202017-03-27%2015.20.37.png?dl=1)

There will be 3 lambdas:

- `hbDtaPost` to catch the `POST` request for first time authentification
- `hbDtaGet` to catch the `GET` requests when someone enters some text
- `hbDtaProcess` to process the text got in `hbDtaGet`

The main reason why we split `hbDtaGet` & `hbDtaProcess` is to avoid to keep the connection between Messenger and the API during the whole process (which takes several seconds in the worst case scenario). So 
`hbDtaGet` invokes `hbDtaProcess` asynchrnously, and then return an HTTP response. `hbDtaProcess` will then send the different answers to the Messenger.

## Echo server + Deployment

As it was my first Messenger bot, I was discovering at the same time. (and first time using Python in Lambda), so we wrote an `Echo` Lambda to answer the exact input. That's easy, but the challenge was to find a correct deployment process to not loose too much time (as the tests had to be done on the server directly).

`deploy.sh` is the solution. It's packing everything which is needed to feed the Lambda, push it to *AWS S3*, and then update the Lambdas.

We could then start the development!

## lambda.py

[lambda.py](https://github.com/aeud/hb-dta/blob/master/lambda/api/lambda.py)