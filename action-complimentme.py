#!/usr/bin/env python2

from hermes_python.hermes import Hermes
from random import randint

MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_ADDR = '{}:{}'.format(MQTT_HOST, str(MQTT_PORT))

INTENT_COMPLIMENT = 'user_gY6zWvG2pdb__complimentMe'
INTENT_COMPLIMENT_REPEAT = 'user_gY6zWvG2pdb__repeatCompliment'
INTENT_COMPLIMENT_SOMEONE = 'user_gY6zWvG2pdb__complimentSomeone'
INTENT_INSULT_SOMEONE = 'user_gY6zWvG2pdb__insultSomeone'
INTENT_INSULT_REPEAT = 'blk_addr:repeatInsult'
INTENT_YES_NO = 'blk_addr:yesNo'
INTENT_RELOAD_COMPLIMENTS = 'blk_addr:reloadCompliments'

CONTINUE_QUESTION = '. Would you like another?'

COMPLIMENTS = []
INSULTS = []
current_mode = '' # "insult" or "compliment"
last_compliment = 'I have not yet had the pleasure'
last_insult = 'That jerk hasn\'t had a taste of this yet'
compliment_mode = 'ordered' # ordered or random, ordered only now because random sucks
last_compliment_number = -1
last_insult_number = -1
in_session = False

def reset_compliment_globals():
    global COMPLIMENTS
    global INSULTS
    global last_compliment_number
    global last_insult_number
    last_compliment_number = -1
    last_insult_number = -1
    COMPLIMENTS = []
    INSULTS = []

def reload_compliments(hermes, message):
    compliment_length = len(COMPLIMENTS)
    insult_length = len(INSULTS)
    reset_compliment_globals()
    load_compliments()
    load_insults()
    compliments_added = len(COMPLIMENTS) - compliment_length
    insults_added = len(INSULTS) - insult_length
    compliment_message = '{} compliments added'.format(str(compliments_added)) \
        if compliments_added >= 0 \
        else '{} compliments removed'.format(str(-compliments_added))
    insult_message = '{} insults added'.format(str(insults_added)) \
        if insults_added >= 0 \
        else '{} insults removed'.format(str(-insults_added))

    hermes.publish_end_session(message.session_id, '{} and {}'.format(compliment_message, insult_message))

def load_compliments():
    for line in open('data/compliments.txt', 'r').readlines():
  	    print(line)
  	    COMPLIMENTS.append(line)

def load_insults():
    for line in open('data/insults.txt', 'r').readlines():
        print(line)
        INSULTS.append(line)

def get_random(items):
    return items[randint(0, len(items) - 1)]

def get_next_compliment():
    global last_compliment_number
    if last_compliment_number >= len(COMPLIMENTS) - 1:
        last_compliment_number = -1
    last_compliment_number += 1
    return COMPLIMENTS[last_compliment_number]


def get_next_insult():
    global last_insult_number
    if last_insult_number >= len(INSULTS) - 1:
        last_insult_number = -1
    last_insult_number += 1
    return INSULTS[last_insult_number]

def get_compliment():
    global last_compliment
    global current_mode
    global in_session
    in_session = True
    if compliment_mode == 'ordered':
        compliment = get_next_compliment()
    else:
        compliment = get_random(COMPLIMENTS)
    print(compliment)
    last_compliment = compliment
    current_mode = 'compliment'
    return compliment

def get_insult():
    global last_insult
    global current_mode
    global in_session
    in_session = True
    if compliment_mode == 'ordered':
        insult = get_next_insult()
    else:
        insult = get_random(INSULTS)
    print(insult)
    last_insult = insult
    current_mode = 'insult'
    return insult

def get_name(message):
    name = message.slots.name.first().value
    return name if name != '' and name != 'unknownword' else 'Unknown Person'

def user_gives_answer(hermes, message):
    if in_session == False:
        print('Not in session, exiting')
        end_session(hermes, message)
    else:
        answer = message.slots.answer.first().value
        print(answer)
        if answer != 'yes':
            if current_mode == 'compliment':
                end_session(hermes, message)
            else:
                end_insult_session(hermes, message)
        else:
            if current_mode == 'compliment':
                compliment(hermes, message)
            else:
                insult(hermes, message)

def end_session(hermes, message):
    global in_session
    in_session = False
    hermes.publish_end_session(message.session_id, None)

def end_insult_session(hermes, message):
    global in_session
    in_session = False
    hermes.publish_end_session(message.session_id, 'Go away or I shall taunt you a second time')

def compliment(hermes, message):
    hermes.publish_continue_session(message.session_id,
        get_compliment() + CONTINUE_QUESTION,
        [INTENT_YES_NO])

def compliment_repeat(hermes, message):
    hermes.publish_end_session(message.session_id, last_compliment)

def compliment_someone(hermes, message):
    hermes.publish_continue_session(message.session_id,
        '{}, {}'.format(get_name(message),get_compliment()) + CONTINUE_QUESTION,
        [INTENT_YES_NO])

def insult(hermes, message):
    hermes.publish_continue_session(message.session_id,
        get_insult() + CONTINUE_QUESTION,
        [INTENT_YES_NO])

def insult_someone(hermes, message):
    hermes.publish_continue_session(message.session_id,
        '{}, {}'.format(get_name(message), get_insult()) + CONTINUE_QUESTION,
        [INTENT_YES_NO])

def insult_repeat(hermes, message):
    hermes.publish_end_session(message.session_id, last_insult)

if __name__ == '__main__':
    load_compliments()
    load_insults()
    with Hermes(MQTT_ADDR) as h:
        h.subscribe_intent(INTENT_COMPLIMENT, compliment) \
        .subscribe_intent(INTENT_COMPLIMENT_REPEAT, compliment_repeat) \
        .subscribe_intent(INTENT_COMPLIMENT_SOMEONE, compliment_someone) \
        .subscribe_intent(INTENT_INSULT_SOMEONE, insult_someone) \
        .subscribe_intent(INTENT_INSULT_REPEAT, insult_repeat) \
        .subscribe_intent(INTENT_YES_NO, user_gives_answer) \
        .subscribe_intent(INTENT_RELOAD_COMPLIMENTS, reload_compliments) \
        .start()
