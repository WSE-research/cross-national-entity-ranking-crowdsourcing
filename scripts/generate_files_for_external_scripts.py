import os
import json
import pandas as pd
from tqdm import tqdm
from utils import execute, transform_sparql_json_to_dataframe, write_json, read_json
import argparse

parser = argparse.ArgumentParser(description='Process command line arguments.')

parser.add_argument('--outlang', dest="outlang", type=str, help='Output language')
parser.add_argument('--datapath', dest="datapath", type=str, help='Relative path to data')

args = parser.parse_args()

output_language = args.outlang
data_path = args.datapath

languages = ["en", "de", "ru"]
wdt_category_uris = list()
data = dict()

for lang in languages:
    with open(os.path.join(data_path, f'wikidata/{lang}_category_entities.json')) as f:
        topics_answers = json.load(f)

    wdt_category_uris += list(topics_answers.keys())
    data[lang] = topics_answers

wdt_category_uris = list(set(wdt_category_uris))

category_uri_to_label = dict()

print("Fetching categories' labels")

for cat_id in tqdm(wdt_category_uris):
    category_uri_to_label_path = os.path.join(data_path, f'utils/category_uri_to_label_{output_language}.json')

    if os.path.isfile(category_uri_to_label_path):
        print("File with categories' labels exists")
        category_uri_to_label = read_json(category_uri_to_label_path)
        break

    print(cat_id, end='\r')

    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label WHERE {{
    <http://www.wikidata.org/entity/{cat_id}> rdfs:label ?label
    FILTER(LANG(?label)="{output_language}")
    }}
    """
    result = transform_sparql_json_to_dataframe(execute(query=query, endpoint_url="https://query.wikidata.org/bigdata/namespace/wdq/sparql"))
    if result.shape[0] > 0:
        label = result.label[0]
        category_uri_to_label[cat_id] = label

write_json(category_uri_to_label, category_uri_to_label_path)

print("For each category get only those entities that have labels in all languages...")

for cat_id in tqdm(wdt_category_uris):
    if cat_id not in category_uri_to_label.keys():
        print(f"Category {cat_id} isn't in the labels list! Skipping...")
        continue
    
    tuples_path = os.path.join(data_path, f'final-crowdsourcing-experiments/{output_language}/{category_uri_to_label[cat_id].replace(" ", "-")}.txt')

    if os.path.exists(tuples_path):
        print("Category exists. Skipping...", end='\r')
        continue

    print(category_uri_to_label[cat_id], end='\n')

    candidate_entities = list()
    
    for lang in languages:
        try:
            candidate_entities += list(set(data[lang][cat_id]["top_entities"]))
        except:
            continue

    final_entities = dict()
    for ent in candidate_entities:
        query_body = '\n'.join(f"<http://www.wikidata.org/entity/{ent}> rdfs:label ?label_{lang} . \n FILTER(LANG(?label_{lang})='{lang}') ." for lang in languages)
        # query_modifiers = " && ".join(f"LANG(?label_{lang})='{lang}'" for lang in languages)
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?label_en ?label_de ?label_ru WHERE {{
        {query_body}
        }}
        """
        print(ent, end='\r')
        result = transform_sparql_json_to_dataframe(execute(query=query, endpoint_url="https://query.wikidata.org/bigdata/namespace/wdq/sparql"))

        if type(result) == pd.DataFrame and result.shape[0] > 0:
            final_entities[ent] = result[f"label_{output_language}"][0]
        else:
            continue

    with open(tuples_path, 'w') as f:
        # write list items line by line
        for uri, label in final_entities.items():
            f.write(label + '\n')

    write_json(final_entities, os.path.join(data_path, f'final-crowdsourcing-experiments/{output_language}/{category_uri_to_label[cat_id].replace(" ", "-")}.json'))