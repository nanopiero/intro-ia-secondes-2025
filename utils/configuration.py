# -*- coding: utf-8 -*-

# Define the class ID to class name mapping
correspondance = {
    0: "nsp",
    1: "ciel vide",
    2: "Cb (même loin)",
    3: "ciel quasi vide",
    4: "Ct",
    10: "brouillard/brume",
    11: "brouillard en nappes",
    12: "St fra",
    13: "St neb",
    20: "Cu fra/hu",
    21: "Cu me/con",
    22: "Cu con/Cb (sous)",
    23: "Cu ra",
    30: "Sc",
    40: "Ac str",
    41: "Ac flo",
    42: "Ac len",
    43: "Ac cas",
    44: "Ac/Sc vol",
    50: "As",
    60: "Ns pluie",
    61: "Pannus",
    70: "Cc str",
    71: "Cc flo",
    72: "Cc len",
    73: "Cc cas",
    74: "Cs neb",
    75: "Ci ou Cs fi",
    80: "Cu/Sc sous",
    81: "Plafond chaotique",
    82: "Ns ou St neb op",
    90: "mélange",
    100: "spécial" # pareidolie/arcus/mammatus/parhélies/éclair/phén optiques
}

group2direction_and_starthour = {
    0: ('S', '08H00'), 1: ('S', '10H00'),  # already done
    2: ('S', '08H20'), 3: ('S', '08H40'), 4: ('S', '09H00'), 5: ('S', '09H20'), 6: ('S', '09H40'),  # new times
    7: ('N', '09H00'), 8: ('E', '09H00'), 9: ('O', '09H00'),  # different targets
    10: ('S', '09H10'), 11: ('S', '09H04'), 12: ('S', '09H02'),  # more precise times
    13: ('S', '09H00')  # for Louis
}

# Explicit value-to-color mapping
value_to_color = {
    0: 'silver',
    1: 'blue', 3: 'blue', 4: 'blue',
    2: 'red',
    10: 'chocolate', 11: 'chocolate',
    12: 'chocolate', 13: 'chocolate',
    20: 'mediumSpringGreen', 21: 'mediumSpringGreen', 22: 'mediumspringgreen', 23: 'hotpink',
    30: 'lime',
    40: 'lightgreen', 41: 'pink', 42: 'hotpink', 43: 'hotpink', 44: 'hotpink',
    50: 'yellow',
    60: 'orange', 61: 'orange', 82: 'orange',
    70: 'turquoise', 71: 'hotpink', 72: 'hotpink', 73: 'hotpink', 74:'aqua', 75:'aqua',
    80: 'olive',
    81: 'salmon',
    90: 'white',
    100:'pink'
}

 
group2sheets = {0: 'https://docs.google.com/spreadsheets/d/1sjvrkLMEY0YXAyXU9Ad8i49J29jCmKkJb85T2pZ2CS8',
                1: 'https://docs.google.com/spreadsheets/d/1sjvrkLMEY0YXAyXU9Ad8i49J29jCmKkJb85T2pZ2CS8',
                2: 'https://docs.google.com/spreadsheets/d/1Npi7H-Y-P60QBODOL8Q5ArQHr5dIn9mOuYv67LLHcNE',
                3: 'https://docs.google.com/spreadsheets/d/1I_ZwJrPt1AO_tQJSX2JBreFFhAlsF7kITH9p_1gDhks',
                4: 'https://docs.google.com/spreadsheets/d/1e1LnjbLKoZ_JxYfGLu1nFIQWyioNt4AV_Y9C1CUqiWI',
                5: 'https://docs.google.com/spreadsheets/d/1unaaeXdGVdC_1JMMVSBUgxc6vdrJzE16lTiP6OBEl04',
                6: 'https://docs.google.com/spreadsheets/d/1odXOBEiNbFQ48NALzTEmCs7LDlBHWARdsivL8rO47fw',
                7: 'https://docs.google.com/spreadsheets/d/1v7gJmdK1AqMelBRaksIcrIN_mDjobH8wxMxfLbiKlS8',
                8: 'https://docs.google.com/spreadsheets/d/1chlVgydwqpQYq44ynEWX_I0QVtWsUaYfwqVSptTD-dA',
                9: 'https://docs.google.com/spreadsheets/d/1x295asse_gh31-EzXQYFUSIkpbLe-hvYwWAxyr1c_ag',
                10: 'https://docs.google.com/spreadsheets/d/1QKZuVjBd1SOmAZvg1zA4vnzLnh8DXVzDouwA941WB2I',
                11: 'https://docs.google.com/spreadsheets/d/1oNurDfrYvCr0hnawUz432Dyh8Mkunk820GiDoa1Sz_E',
                12: 'https://docs.google.com/spreadsheets/d/1EgmnmcX8jMXZmz6s_-oW473FnuT3HgPjlSnqCcJTrP4',
                13 : 'https://docs.google.com/spreadsheets/d/1KT4RXpX3FkR2APlGXhD54euEpPWHbFZKrxoWdFzeqog'}


