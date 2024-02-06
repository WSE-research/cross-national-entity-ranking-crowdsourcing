import logging
import pandas as pd
from utils import execute_query, read_file, is_latin, remove_special_characters, write_json, to_plural_english, to_plural_german, to_plural_russian

DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"
LANGUAGE_CODES = ['en', 'de', 'ru']# ['de', 'en', 'es', 'fa', 'fr', 'it', 'jp', 'ru', 'zh',  'pt', 'pl'] # ISO 639-1

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

lang_template_dict = {
    "en": ["List me all {0}"],
    "de": ["Liste mir alle {0}"],
    "ru": ["Список всех {0}"]
}

lang_plural_func_dict = {
    "en": to_plural_english,
    "de": to_plural_german,
    "ru": to_plural_russian
}

def run_all():
    get_classes_query = read_file("../sparql/dbpediaOntologyClasses.rq")
    classes_response = execute_query(get_classes_query, DBPEDIA_ENDPOINT)
    classes = list()
    for result in classes_response['results']['bindings']:
        if all([is_latin(c) for c in remove_special_characters(result['ontologyClass']['value'])]):
            classes.append(result['ontologyClass']['value'])
    
    get_instances_query = read_file("../sparql/dbpediaInstancesOfOntologyClasses.rq")
    id_ = 0
    questions_list = list()
    for cls in classes:
        logger.info("Fetching instances of class: {}".format(cls))
        question_list = list()
        query = get_instances_query.replace("<dboClass>", "<" + cls + ">")
        answers = execute_query(query, DBPEDIA_ENDPOINT)
        for lang in LANGUAGE_CODES:
            # get label of the class via sparql
            label_query = read_file("../sparql/dbpediaGetLabel.rq").replace("<dboClass>", "<" + cls + ">").replace("<langCode>", lang)
            label_response = execute_query(label_query, DBPEDIA_ENDPOINT)
            label = "[NO LABEL]"
            for result in label_response['results']['bindings']:
                label = result['label']['value']
                break

            plural_label = lang_plural_func_dict[lang](label) # todo: finish "to plural" functions or use GPT-3

            question_list.append({
                "language": lang,
                "string": lang_template_dict[lang][0].format(plural_label), 
            })
        
        questions_list.append({ # QALD-JSON format
            "id": id_,
            "question": question_list,
            "query": query,
            "answers": [answers]
        })

        id_ += 1

        write_json(questions_list, "../data/dbpedia/dbpedia-ontology-classes.json")
            

def run_top_level():
    get_top_level_query = read_file("../sparql/dbpediaOntologyTopLevel.rq")
    top_level_response = execute_query(get_top_level_query, DBPEDIA_ENDPOINT)
    top_level_classes = list()
    for result in top_level_response['results']['bindings']:
        if all([is_latin(c) for c in remove_special_characters(result['ontologyClass']['value'])]):
            top_level_classes.append(result['ontologyClass']['value'])
    
    get_instances_query = read_file("../sparql/dbpediaInstancesOfOntologyClasses.rq")
    for cls in top_level_classes:
        logger.info("Fetching instances of class: {}".format(cls))
        for lang in LANGUAGE_CODES:
            query = get_instances_query.replace("<dboClass>", "<" + cls + ">").replace("<languageCode>", lang)
            results = execute_query(query, DBPEDIA_ENDPOINT)
            uris, labels = list(), list()
            for result in results['results']['bindings']:
                uris.append(result['instance']['value'])
                labels.append(result['label']['value'])
            df = pd.DataFrame({"uri": uris, "label": labels})
            df.to_csv("../data/dbpedia/{}-{}.csv".format(lang, cls.replace("http://dbpedia.org/ontology/", "")), index=False)
            
if __name__ == "__main__":
    run_all()