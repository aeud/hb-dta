# HB DTA

*Unfortunately I didn't have time to submit and make the Messenger app to be validated, so for you to use the bot directly on Messenger, please send me your Facebook ID, I'll add you as a developer of the app, and you'll be able to try it. There is also a demo bellow.*

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

![infrastructure](https://www.dropbox.com/s/hty9db1vhmm1wm4/infrastructure.jpg?dl=1)

## Chat process

Before coding, let's analyse what we'll have to develop

![flow](https://www.dropbox.com/s/iypbrdn87o7jszj/Screenshot%202017-03-27%2015.20.37.png?dl=1)

There will be 2 lambdas:

- `hbDtaWS` to catch the `GET` & `POST` from Messenger: `GET` for the authentification challenge, and `POST` for the messages
- `hbDtaBot` to process the text got in `hbDtaGet`

The main reason why we split `hbDtaWS` & `hbDtaBot` is to avoid to keep the connection between Messenger and the API during the whole process (which takes several seconds in the worst case scenario). So 
`hbDtaWS` invokes `hbDtaBot` asynchrnously, and then return an HTTP response. `hbDtaBot` will then send the different answers to the Messenger.

## Echo server + Deployment

As it was my first Messenger bot, I was discovering at the same time. (and first time using Python in Lambda), so we wrote an `Echo` Lambda to answer the exact input. That's easy, but the challenge was to find a correct deployment process to not loose too much time (as the tests had to be done on the server directly).

`deploy.sh` is the solution. It's packing everything which is needed to feed the Lambda, push it to *AWS S3*, and then update the Lambdas.

We could then start the development!

## Code

- Web server: [hb_dta_ws.py](https://github.com/aeud/hb-dta/blob/master/hb_dta_ws.py)
- Bot: [hb_dta_bot.py](https://github.com/aeud/hb-dta/blob/master/hb_dta_bot.py)

## A small word about the recommendations

Recommendations is very complicated when using an API, because they are written to describe the data, not to analyse it. At the beginning, the idea was to dump the enough amount of data (probably to a relational **PostgreSQL**), and run some queries on the top of it.

The only limit was that 1 request / sec quota from *OpenDota*, which was beatable by using *Lambdas*, but still, it was quite long.

However, after having read the *OpenDota API documentation*, the solution was there: the `explorer` method let us query directly their *PostgreSQL* database. The `schema` method gave me the tables, and after a quick draft of the tables, I could write the recommendation query:

**Based on a player's most player heroes, and on the past matches, which cominations hero / item are the best?**

```
SELECT
    h.name hero,
    i.name item,
    SUM(pm.kills) kills
FROM
    player_matches pm,
    items i,
    heroes h
WHERE
    i.id IN (pm.item_0, pm.item_1, pm.item_2, pm.item_3, pm.item_4, pm.item_5)
    AND h.id = pm.hero_id
    AND pm.hero_id IN (12432, 432423, 32432423) -- player's top heroes
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 10
```

## Demo

![demo](https://www.dropbox.com/s/f5r5v6npgm73sm1/test-chat.gif?dl=1)