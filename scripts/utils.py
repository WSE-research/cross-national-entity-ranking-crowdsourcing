import pandas as pd
import logging
import json
from time import sleep
from SPARQLWrapper import SPARQLWrapper, JSON

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def to_plural_german(word):
    return word

def to_plural_russian(word):
    return word

def to_plural_english(word):
    if word.endswith('y'):
        return word[:-1] + 'ies'
    elif word.endswith('s'):
        return word + 'es'
    else:
        return word + 's'

def write_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def read_json(filename):
    with open(filename) as f:
        return json.load(f)

def read_file(file_name):
    with open(file_name, 'r') as f:
        return f.read()

def is_latin(char):
    return char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def remove_special_characters(string):
    return ''.join(c for c in string if c.isalnum() or c == '_')

def execute(query: str, endpoint_url: str = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'):
    """
    https://dbpedia.org/sparql
    https://query.wikidata.org/bigdata/namespace/wdq/sparql
    """
    agent_header = {'User-Agent': 'wiki_parser_online/0.17.1 (https://deeppavlov.ai;'
                                        ' info@deeppavlov.ai) deeppavlov/0.17.1'}
    timeout = 100
    e = ''
    try:
        sparql = SPARQLWrapper(endpoint_url)
        sparql.agent = str(agent_header)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(timeout)
        response = sparql.query().convert()
        return response
    except Exception as e:
        e = str(e)
        print(e)
        return None
            
def transform_sparql_json_to_dataframe(response: dict):
    df_dict = dict()
    try:
        data = response["results"]["bindings"]
        for i in data:
            for k, v in i.items():
                if k not in df_dict.keys():
                    df_dict[k] = list()
                df_dict[k].append(v.get("value"))
    except Exception as e:
        print(str(e))
        return None
    
    return pd.DataFrame.from_dict(df_dict)