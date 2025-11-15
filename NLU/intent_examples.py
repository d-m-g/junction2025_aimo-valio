"""
Intent Examples Database
Example sentences for each intent to enable semantic similarity matching
"""

INTENT_EXAMPLES = {
    'confirm_substitution': {
        'en': [
            'Yes, I accept the replacement',
            'I will take the substitute',
            'That works for me',
            'Go ahead with the replacement',
            'I agree to the substitute',
            'Yes, please send the replacement',
            'I will accept it',
            'Sounds good, I will take it',
            'Okay, I will take the substitute',
            'I want the replacement'
        ],
        'fi': [
            'Kyllä, hyväksyn korvauksen',
            'Otan korvauksen',
            'Sopii minulle',
            'Hyväksyn vaihtoehdon',
            'Joo, lähetä korvaus',
            'Otan sen',
            'Sama käy'
        ],
        'sv': [
            'Ja, jag accepterar ersättningen',
            'Jag tar ersättningen',
            'Det fungerar',
            'Gå vidare med ersättningen',
            'Jag accepterar det',
            'Okej, skicka ersättningen'
        ]
    },
    'reject_substitution': {
        'en': [
            'No, I do not want a substitute',
            'I decline the replacement',
            'I do not want it',
            'No thanks, skip it',
            'I do not need a replacement',
            'Leave it out',
            'Do not send a substitute',
            'I do not want the replacement',
            'No, skip the replacement',
            'Cancel that item'
        ],
        'fi': [
            'Ei, en halua korvausta',
            'Hylkään korvauksen',
            'En halua sitä',
            'Ei kiitos, ohita se',
            'Jätä pois',
            'Älä lähetä korvausta'
        ],
        'sv': [
            'Nej, jag vill inte ha ersättning',
            'Jag avvisar ersättningen',
            'Jag vill inte ha den',
            'Nej tack, hoppa över',
            'Skicka inte ersättning'
        ]
    },
    'request_callback': {
        'en': [
            'I need to speak to someone',
            'Can I talk to a human',
            'I want to speak to customer service',
            'Please call me back',
            'I need to talk to an agent',
            'Connect me to a person',
            'I want to speak to someone about my order',
            'Can you call me',
            'I need human assistance',
            'Let me speak to a representative'
        ],
        'fi': [
            'Haluan puhua jonkun kanssa',
            'Voinko puhua ihmisen kanssa',
            'Tarvitsen asiakaspalvelun',
            'Soita minulle takaisin',
            'Yhdistä minut henkilöön'
        ],
        'sv': [
            'Jag behöver prata med någon',
            'Kan jag prata med en människa',
            'Jag vill prata med kundtjänst',
            'Ring mig tillbaka',
            'Koppla mig till en person'
        ]
    },
    'report_issue': {
        'en': [
            'I did not receive my order',
            'My delivery is missing items',
            'I see only 2 boxes, not 3',
            'The package arrived damaged',
            'I did not get what I ordered',
            'Something is wrong with my delivery',
            'My order is incomplete',
            'I received the wrong product',
            'The items are damaged',
            'I see that there is only 2 boxes of milk, not 3',
            'I have a problem with my order',
            'My delivery has issues'
        ],
        'fi': [
            'En saanut tilaukseni',
            'Toimituksesta puuttuu tuotteita',
            'Näen vain 2 laatikkoa, ei 3',
            'Paketti saapui vahingoittuneena',
            'Sain väärän tuotteen',
            'Tilaukseni on epätäydellinen'
        ],
        'sv': [
            'Jag fick inte min beställning',
            'Min leverans saknar varor',
            'Jag ser bara 2 lådor, inte 3',
            'Paketet anlände skadat',
            'Jag fick fel produkt',
            'Min beställning är ofullständig'
        ]
    },
    'confirm_delivery': {
        'en': [
            'I received everything',
            'All items arrived',
            'Delivery is complete',
            'Everything is here',
            'All good, received all items',
            'Perfect, got everything',
            'Delivery successful',
            'All items received',
            'Everything arrived safely'
        ],
        'fi': [
            'Sain kaiken',
            'Kaikki tuotteet saapuivat',
            'Toimitus valmis',
            'Kaikki on täällä',
            'Kaikki hyvin'
        ],
        'sv': [
            'Jag mottog allt',
            'Alla varor anlände',
            'Leverans klar',
            'Allt är här',
            'Allt bra'
        ]
    },
    'query_order_status': {
        'en': [
            'Where is my order',
            'When will my delivery arrive',
            'What is the status of my order',
            'I need to get it tomorrow',
            'When is my order coming',
            'Track my order',
            'Check order status',
            'Where is my package',
            'When will it be delivered',
            'I have to get it tomorrow'
        ],
        'fi': [
            'Missä on tilaukseni',
            'Milloin toimitus saapuu',
            'Mikä on tilaukseni tila',
            'Tarvitsen sen huomenna',
            'Milloin tilaus tulee'
        ],
        'sv': [
            'Var är min beställning',
            'När kommer min leverans',
            'Vad är status på min beställning',
            'Jag behöver den imorgon',
            'När kommer den'
        ]
    },
    'query_substitution': {
        'en': [
            'What replacement did you suggest',
            'Tell me about the substitute',
            'What is the replacement product',
            'Which substitute are you offering',
            'What did you recommend',
            'Show me the replacement option',
            'What is the alternative'
        ],
        'fi': [
            'Mikä korvaus ehdotettiin',
            'Kerro korvauksesta',
            'Mikä on korvaava tuote',
            'Mitä suosititte'
        ],
        'sv': [
            'Vad för ersättning föreslog ni',
            'Berätta om ersättningen',
            'Vilken ersättning erbjuder ni',
            'Vad rekommenderade ni'
        ]
    },
    'thank_you': {
        'en': [
            'Thank you very much',
            'Thanks a lot',
            'I appreciate it',
            'Thank you for your help',
            'Much appreciated',
            'Thanks',
            'Thank you so much'
        ],
        'fi': [
            'Kiitos paljon',
            'Kiitoksia',
            'Arvostan sitä',
            'Kiitos avusta'
        ],
        'sv': [
            'Tack så mycket',
            'Tusen tack',
            'Jag uppskattar det',
            'Tack för hjälpen'
        ]
    },
    'change_delivery': {
        'en': [
            'I need to get it tomorrow',
            'Can you deliver on Monday instead',
            'Change delivery time to next week',
            'I want to reschedule the delivery',
            'Can we change the delivery date',
            'Move delivery to tomorrow',
            'I have to get it tomorrow',
            'Change delivery address',
            'Deliver at a different time',
            'Reschedule for next week'
        ],
        'fi': [
            'Tarvitsen sen huomenna',
            'Voitteko toimittaa maanantaina',
            'Muuta toimitusaikaa',
            'Haluan siirtää toimituksen',
            'Vaihda toimituspäivää'
        ],
        'sv': [
            'Jag behöver den imorgon',
            'Kan ni leverera på måndag',
            'Ändra leveranstid',
            'Jag vill omplanera leveransen',
            'Flytta leverans till imorgon'
        ]
    },
    'cancel_order': {
        'en': [
            'I want to cancel my order',
            'Cancel the order',
            'Stop the delivery',
            'Do not deliver',
            'Cancel order number 12345',
            'I need to cancel',
            'Please cancel my order',
            'I want to cancel'
        ],
        'fi': [
            'Haluan peruuttaa tilaukseni',
            'Peruuta tilaus',
            'Lopeta toimitus',
            'Älä toimita',
            'Peruuta tilaus numero'
        ],
        'sv': [
            'Jag vill avbryta min beställning',
            'Avbryt beställningen',
            'Stoppa leveransen',
            'Leverera inte',
            'Avbryt beställning nummer'
        ]
    },
    'query_products': {
        'en': [
            'Do you have milk available',
            'Is milk in stock',
            'What products do you have',
            'Tell me about your products',
            'What items are available',
            'Do you sell milk',
            'What products can I get',
            'Is product X available'
        ],
        'fi': [
            'Onko maitoa saatavilla',
            'Onko maito varastossa',
            'Mitä tuotteita teillä on',
            'Kerro tuotteistanne',
            'Mitkä tuotteet ovat saatavilla'
        ],
        'sv': [
            'Har ni mjölk tillgänglig',
            'Finns mjölk i lager',
            'Vilka produkter har ni',
            'Berätta om era produkter',
            'Vilka varor finns tillgängliga'
        ]
    },
    'provide_feedback': {
        'en': [
            'I want to give feedback',
            'I would like to leave feedback',
            'Let me provide some feedback',
            'I have feedback about the service',
            'I want to share my experience',
            'Can I give feedback'
        ],
        'fi': [
            'Haluan antaa palautetta',
            'Haluan jättää palautetta',
            'Anna minun antaa palautetta',
            'Minulla on palautetta palvelusta'
        ],
        'sv': [
            'Jag vill ge feedback',
            'Jag skulle vilja lämna feedback',
            'Låt mig ge feedback',
            'Jag har feedback om tjänsten'
        ]
    },
    'greeting': {
        'en': [
            'Hello',
            'Hi there',
            'Good morning',
            'Hey',
            'Greetings'
        ],
        'fi': [
            'Hei',
            'Moi',
            'Hyvää päivää',
            'Terve'
        ],
        'sv': [
            'Hej',
            'Hallå',
            'God morgon',
            'Hejsan'
        ]
    },
    'unknown': {
        'en': [
            # Keep empty or add generic fallback examples
        ],
        'fi': [],
        'sv': []
    }
}

