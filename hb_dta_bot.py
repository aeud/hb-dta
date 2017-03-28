# -*- coding: utf-8 -*-
import logging
import json
import requests
import re
import time
import os
from inflection import humanize

"""
Setup the logger
"""
logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""
LAMBDA Definition: hbDtaBot
hb_dta_bot will parse the event payload and execute receive_message method
for each received message
"""
def handler(event, context):
    logger.info(json.dumps(event))

    body = event.get("body-json")

    if body.get("object") != "page":
        return None # break

    for entry in body.get("entry"):
        for event in entry.get("messaging"):
            if event.get("message"):
                receive_message(event)
    
    return None # break



def receive_message(message):
    if message.get("message").get("quick_reply"):
        text = message.get("message").get("quick_reply").get("payload")
    else:
        text = message.get("message").get("text")
    sender = message.get("sender")
    sender_id = sender.get("id")
    send_indicator(sender_id, "mark_seen")
    send_indicator(sender_id, "typing_on")

    if not re.match('\d{5}', text): # We guess user entered a name
        bot_deal_with_a_name(text, sender_id)
    else: # Otherwise it's a number (or many)
        account_ids = re.findall('\d+', text)
        if len(account_ids) > 1: # If many
            bot_deal_with_several_numbers(account_ids, sender_id)
        else: # Otherwise
            account_id = account_ids[0]
            bot_deal_with_one_number(account_id, sender_id)
            

"""
If there is a name, use the `exporer` API, and try to get matches.
If there is several possibilities, ask for the user to choose one of them.
Otherwise, if no result, appologize; if only one result, go to `bot_deal_with_one_number`
"""
def bot_deal_with_a_name(text, sender_id):
    send_text_message(sender_id, "Thanks, give me a moment, I'm checking this name")
    send_indicator(sender_id, "typing_on")
    matches = request_opendota("/search", params={
        'q': text,
    })
    if len(matches) > 1:
        options = []
        for m in matches[:10]:
            options.append({
                'content_type': "text",
                'title': m.get("personaname"),
                'payload': m.get("account_id"),
                'image_url': m.get("avatarfull"),
            })
        send_text_message(sender_id, "I found few matches, do you mean one of them?", options=options)
    elif len(matches) == 1:
        bot_deal_with_one_number(m.get("account_id"), sender_id)
    else:
        send_text_message(sender_id, "Sorry I found no match, would you like to try another name?")

"""
If there are several numbers in the text, we'll ask the user to choose only one of them.
TODO: Possibility to get comparisons between 2 or more players.
"""
def bot_deal_with_several_numbers(account_ids, sender_id):
    options = []
    i = 0
    for account_id in account_ids[:10]:
        player = get_player(account_id)
        if player.get("profile"):
            i += 1
            options.append({
                'content_type': "text",
                'title': player.get("profile").get("personaname"),
                'payload': player.get("profile").get("account_id"),
                'image_url': player.get("profile").get("avatarfull"),
            })
    if i > 0:
        send_text_message(sender_id, "You referred to different users, could you please choose one of them?", options=options)
    else:
        send_text_message(sender_id, "Unfortunately, I cannot find any Dota player...")        

"""
Get statistics avout a player, his/her name, picture, most player heroes, and some recommendations.
"""
def bot_deal_with_one_number(account_id, sender_id):
    send_text_message(sender_id, "Let me see what I have about this player...")
    send_indicator(sender_id, "typing_on")
    player = get_player(account_id)
    if player.get("profile"):
        send_text_message(sender_id, "account id: %s" % account_id)

        name = player.get("profile").get("personaname")

        send_text_message(sender_id, "I know this person, this is %s 👾" % (
            name,
        ))

        send_text_message(sender_id, "Oh, I even have a picture")
        send_indicator(sender_id, "typing_on")

        send_image(
            sender_id,
            player.get("profile").get("avatarfull"),
        )

        send_text_message(sender_id, "I love it!")

        send_text_message(sender_id, "Let me check about his/her heroes...")
        send_indicator(sender_id, "typing_on")

        player_heroes = get_player_heroes(account_id)

        if len(player_heroes) <= 5:
            send_text_message(sender_id, "%s used %d heroes. Let me find some info about them." % (
                name,
                len(player_heroes),
            ))
        else:
            send_text_message(sender_id, "%s used %d heroes, that's impressive. Let me find some of them." % (
                name,
                len(player_heroes),
            ))

        send_indicator(sender_id, "typing_on")
        all_heroes = get_heroes_hash()

        for i, hero in enumerate(player_heroes[:5]):
            hero_ = all_heroes[int(hero.get("hero_id"))]
            if i == 0:
                mess = "%s played %d times with %s" % (
                    name,
                    hero.get("games"),
                    hero_.get("localized_name"),
                )
            else:
                mess = "%d times with %s" % (
                    hero.get("games"),
                    hero_.get("localized_name"),
                )
                send_indicator(sender_id, "typing_on")
            send_text_message(sender_id, mess)
            send_indicator(sender_id, "typing_on")

        moves = recommended_moves(player_heroes[:5])
        if len(moves) > 0:
            send_text_message(sender_id, "Based on these heroes, I would suggest some nice item combinations: 🔪")
            send_indicator(sender_id, "typing_on")
            mess = ""
            for move in moves[:3]:
                mess += "%s with %s\n" % (
                humanize(move.get("hero").replace("npc_dota_hero_", "")),
                humanize(move.get("item").replace("item_", "")),
            )
            send_text_message(sender_id, mess)

        send_text_message(sender_id, "I hope that was helpful 🙃")
        send_text_message(sender_id, "I'm happy to help again!")
    else:
        send_text_message(sender_id, "Unfortunately, I cannot find anything. Are you sure this account belongs to a Dota player?")
    

def get_player(account_id):
    return request_opendota("/players/%s" % account_id)

def get_player_heroes(account_id):
    return [h for h in request_opendota("/players/%s/heroes" % account_id) if h.get("games") > 0]

def get_heroes():
    return request_opendota("/heroes")

def get_heroes_hash():
    h = {}
    heroes = get_heroes()
    for hero in heroes:
        h[hero.get("id")] = hero
    return h

def recommended_moves(player_heroes):
    sql = """
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
        AND pm.hero_id IN (%s)
    GROUP BY 1, 2
    ORDER BY 3 DESC
    LIMIT 10
    """
    ids = []
    for h in player_heroes:
        ids.append(h.get("hero_id"))
    return request_opendota("/explorer", {
        'sql': sql % ",".join(ids)
    }).get("rows")

"""
https://docs.opendota.com/
"""
def request_opendota(path, params=None):
    return requests.get("%s/%s" % (
        os.environ.get("OPENDOTA_ENDPOINT"),
        path,
    ), params=params).json()

"""
send_text_message will send a simple text message
if options are specified, the messewnger will display those options
"""
def send_text_message(sender_id, message_text, options=None):
    payload = {
        'recipient': {
            'id': sender_id,
        },
        'message': {
            'text': message_text[:640],
        },
    }
    if options is not None:
        payload["message"]["quick_replies"] = options
    return call_send_api(payload)

"""
send_image will upload an image to the messenger
"""
def send_image(sender_id, image_url):
    return call_send_api({
        'recipient': {
            'id': sender_id,
        },
        'message': {
            'attachment': {
                'type': "image",
                'payload': {
                    'url': image_url,
                },
            },
        },
    })

"""
send_indicator will execute the action on the messenger
https://developers.facebook.com/docs/messenger-platform/send-api-reference/sender-actions
"""
def send_indicator(sender_id, action):
    call_send_api({
        'recipient': {
            'id': sender_id,
        },
        'sender_action': action,
    })

"""
call_send_api sends the payload to FB Messenger API
"""
def call_send_api(payload):
    url = "%s?access_token=%s" % (
        os.environ.get("FB_ENDPOINT"),
        os.environ.get("PAGE_TOKEN"),
    )
    print url
    print payload
    return requests.post(
        url,
        json=payload
    )