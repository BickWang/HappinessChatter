#!/usr/bin/env python
# coding: utf-8

# In[11]:


import pandas, sqlite3, random

conn = sqlite3.connect('happiness.db')
c = conn.cursor()

df = pandas.read_csv('happiness2020.csv')
df.to_sql('happiness', conn, if_exists='replace', index=False)


# In[12]:


def find_countries(params):
    # Create the base query
    query = 'SELECT * FROM happiness'
    t = tuple()
    # Add filter clauses for each of the parameters
    if len(params) > 0:
        filters = ["{}=?".format(k) for k in params]
        t += tuple(params.values())
        query += " WHERE " + " and ".join(filters)
    # Open connection to DB
    conn = sqlite3.connect("happiness.db")
    # Create a cursor
    c = conn.cursor()
    # Execute the query
    c.execute(query, t)
    # Return the results
    return c.fetchall()


# In[13]:


from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config

# Create a trainer that uses this config
trainer = Trainer(config.load("config_spacy.yml"))

# Load the training data
training_data = load_data('demo-rasa.json')

# Create an interpreter by training the model
interpreter = trainer.train(training_data)


# In[14]:


def sliceindex(x):
    i = 0
    for c in x:
        if c.isalpha():
            i = i + 1
            return i
        i = i + 1

def upperfirst(x):
    i = sliceindex(x)
    return x[:i].upper() + x[i:]


# In[17]:


def send_message(policy, state, message, current):
    print("USER : {}".format(message))
    new_state, response, current = respond(policy, state, message, current)
    print("BOT : {}".format(upperfirst(response)))
    return new_state, current, response

CURRENT_COUNTRY = None
INIT = 0
COUNTRY_SEARCH = 1

policy = {
    (INIT, "country_search"): (COUNTRY_SEARCH, random.choice([" Do you want more details about them?", " Want to know more?",
                                                             " Say yes for more info!"])),
    (INIT, "greetings"): (INIT, " Yoo! I'm born for providing informations about happiness levels in the world!"),
    (INIT, "none"): (INIT, random.choice([" I'm sorry - I'm not sure how to help you", " Sorry I'm not NATRUAL enough QmQ", 
                                          " Can you paraphrase a little bit?"])),
    (INIT, "affirm"): (INIT, random.choice([" I'm sorry - I'm not sure how to help you", " Sorry I'm not NATRUAL enough QmQ", 
                                          " Can you paraphrase a little bit?"])),
    (INIT, "deny"): (INIT, random.choice([" I'm sorry - I'm not sure how to help you", " Sorry I'm not NATRUAL enough QmQ", 
                                          " Can you paraphrase a little bit?"])),
    (INIT, "compare"): (INIT, " Sorry, I'm not natural enough to understand such comparisons..."),
    (INIT, "bye"): (INIT, " Hail 2 Uuuuu!"),
    (COUNTRY_SEARCH, "country_search"): (COUNTRY_SEARCH, random.choice([" Do you want more details about them?", " Want to know more?",
                                                             " Say yes for more info!"])),
    (COUNTRY_SEARCH, "affirm"): (INIT, random.choice([" What else can I help you?", " Any other questions?",
                                                             " I'm ready for more questions!"])),
    (COUNTRY_SEARCH, "deny"): (INIT, random.choice([" Ok, What else can I help you?", " Any other questions?",
                                                             " That's fine! I'm ready for more questions!"])),
    (COUNTRY_SEARCH, "none"): (COUNTRY_SEARCH, " Sorry I don't know... omo"),
    (COUNTRY_SEARCH, "compare"): (INIT, " Sorry, I'm not natural enough to understand this comparison..."),
    (COUNTRY_SEARCH, "bye"): (INIT, " Wish you happy! Hail 2 U!"),
    (COUNTRY_SEARCH, "greetings"): (INIT, " Yoo! I'm born for providing informations about happiness levels in the world!"),
}

def respond(policy, state, message, current):
    
    intent = interpret(message)
    
    (new_state, response) = policy[(state, intent)]
    
    if intent == "country_search":
        obj = interpreter.parse(message)
        entities = obj["entities"]
        # Initialize an empty params dictionary
        params = {}
        
        # Fill the dictionary with entities
        for ent in entities:
            params[ent["entity"]] = str(ent["value"])
        # Find hotels that match the dictionary

        results = find_countries(params)
        # Get the names of the hotels and index of the response
        
        responses = [
            "I'm sorry :( Couldn't find any country like that", 
            'Here we have {} as your answer!',  
            '{} qualifies, but I know others too :)'
        ]
        
        current = results
        n = min(len(results),2)
        if n == 0:
            return state, responses[0], current
        elif n == 1:
            curr = current
            current = current[0]
            response = responses[1].format(current[0].capitalize()) + " {} is a country belonging to the {}. It has {} happiness overall, due to its {} GDP, {} social support, {} life expectancy, {} freedom, {} generosity, and {} corruption prevention.".format(current[0].capitalize(), current[2].capitalize(), current[3], current[4], current[5], current[6], current[7], current[8], current[9],)
            current = curr
            return state,response + " Are you interested in any other countries?",current
        else:
            response2 = responses[n].format(random.choice(current)[0])
            return new_state, response2 + response, current
    
    if intent == "affirm" and state is COUNTRY_SEARCH:
        if len(current) == 1:
            curr = current
            current = current[0]
            response2 = "{} is a country belonging to the {}. It has {} happiness overall, due to its {} GDP, {} social support, {} life expectancy, {} freedom, {} generosity, and {} corruption prevention.".format(current[0], current[2].capitalize(), current[3], current[4], current[5], current[6], current[7], current[8], current[9],)
            current = curr
            return new_state, response2 + response, current
        names= [cur[0].capitalize() for cur in current]
        response2 = "They are " + ', '.join(map(str,names)) + random.choice([". Do you need an example?", ". An example may help?"])
        current = [random.choice(current)]
        return state, response2, current
    
    if intent == "compare" and current is not None and len(current)!= 0 :
        ent = interpreter.parse(message)["entities"]
        if len(ent) == 1:
            country1 = current[0]
            name2 = ent[0]["value"]
            country2 = find_countries({"Country": name2})[0]
            results = []
            for index in range(3, 10):
                results.append(comparator(country1[index], country2[index]))
            if 1 not in results:
                if 2 not in results:
                    response2 = "{} and {} are as happy on the same level.".format(country1[0].capitalize(), country2[0].capitalize(), country2[0].capitalize(), country1[0].capitalize())
                    return new_state, response2, current
                else:
                    response2 = "{} has generally happier conditions than {}.".format(country2[0].capitalize(), country1[0].capitalize())
                    return new_state, response2, current
            elif 2 not in results:
                response2 = "{} has generally happier conditions than {}.".format(country1[0].capitalize(), country2[0].capitalize())
                return new_state, response2, current
            else:
                response2 = "Compared to {}, {} has ".format(country2[0].capitalize(), country1[0].capitalize())
                list1 = translator(results)
                list2 = [" happiness, ", " GDP, ", " social support, ", " life expectancy, ", " freedom, ", " generosity, ", " corruption prevention."]
                for i in range(6):
                    response2 += list1[i] + list2[i]
                response2 += "and " + list1[6] + list2[6] + " Hope it may help! XD"
                return new_state, response2, current
        elif len(ent) == 2:
            name1 = ent[0]["value"]
            name2 = ent[1]["value"]
            country1 = find_countries({"Country": name1})[0]
            country2 = find_countries({"Country": name2})[0]
            results = []
            for index in range(3, 10):
                results.append(comparator(country1[index], country2[index]))
            if 1 not in results:
                if 2 not in results:
                    response2 = "{} and {} are as happy on the same level.".format(country1[0].capitalize(), country2[0].capitalize(), country2[0].capitalize(), country1[0].capitalize())
                    return new_state, response2, current
                else:
                    response2 = "{} has generally happier conditions than {}.".format(country2[0].capitalize(), country1[0].capitalize())
                    return new_state, response2, current
            elif 2 not in results:
                response2 = "{} has generally happier conditions than {}.".format(country1[0].capitalize(), country2[0].capitalize())
                return new_state, response2, current
            else:
                response2 = "{} has ".format(country1[0].capitalize())
                list1 = translator(results)
                list2 = [" happiness, ", " GDP, ", " social support, ", " life expectancy, ", " freedom, ", " generosity, ", " corruption prevention."]
                for i in range(6):
                    response2 += list1[i] + list2[i]
                response2 += "and " + list1[6] + list2[6] + " Hope it may help! XD"
                return new_state, response2, current
        else:
            return new_state, "Sorry, I could not understand this comparison. Can you paraphrase a little bit?", current
    return new_state, response, current

def interpret(message):
    msg = message.lower()
    if "what can you do" in msg:
        intent = "greetings"
    elif "bye" in msg:
        intent = "bye"
    else:
        intent = interpreter.parse(msg)["intent"]["name"]
    
    return intent

def comparator(string1, string2):
    if string1 == "low":
        if string2 == "low":
            return 0
        else:
            return 2
    elif string1 == "medium":
        if string2 == "low":
            return 1
        elif string2 == "medium":
            return 0
        else:
            return 2
    else:
        if string2 == "high":
            return 0
        else:
            return 1
        
def translator(array):
    for ele in range(len(array)):
        if array[ele] == 0:
            array[ele] = "similar"
        elif array[ele] == 1:
            array[ele] = "better"
        else:
            array[ele] = "worse"
    return array


# In[34]:


import telebot

bot = telebot.TeleBot("1270493023:AAEZ7wZRiDCjPrukwnChl_BVJhuq2hz6Cv8")
current = None
state = INIT

@bot.message_handler(func=lambda m: True)
def auto_reply(msg):
    global state
    global current
    state, current, new_msg = send_message(policy, state, msg.text, current)
    bot.reply_to(msg, new_msg)
bot.polling()

