import requests
import xml.etree.ElementTree as ET
import os
import glob
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
import string
from nltk.corpus import stopwords
import json
import re
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from adjustText import adjust_text

# Load data from a JSON file
def load_data(file):
    with open(file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return (data)

# Write data to a JSON file
def write_data(file, data):
    with open(file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

# Give the PMID of an article from PubMed and retrieves the ID of the same article in the GEO database
def get_geo_id(pmid):
    elink_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "db": "gds",
        "linkname": "pubmed_gds",
        "id": pmid,
        "retmode": "xml"
    }

    response = requests.get(elink_url, params)
    
    # Check if there was any error with the request
    if response.status_code != 200:
        print(f"Couldn't get article with PMID: {pmid}")
        return None

    # Parse the XML response and retrieve the GEO database id
    root = ET.fromstring(response.content)
    geo_id = root.findtext('.//Link/Id')
    
    if geo_id is None:
        print(f"Couldn't get GEO database ID for article with PMID: {pmid}")
        return None
    
    return geo_id


# Give the GEO database ID for an article and retrieve the GSE ID
def get_GSE_id(geo_id):
    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    esummary_params = {
        "db" : "gds",
        "id" : str(geo_id).strip(),
        "retmode" : "xml"
    }

    response = requests.get(esummary_url, esummary_params)

    # Check if there was any error with the request
    if response.status_code != 200:
        print(f"Couldn't access GEO database for id: {geo_id}")
        return None

    # The info is under the DocSum node
    root = ET.fromstring(response.content)
    docsum = root.find('.//DocSum')
    
    # Search for the GSE ID; it is stored under the tag name 'Accession'
    GSE_id = None
    for item in docsum.findall('Item'):
        field_name = item.attrib.get("Name")
        if field_name == "Accession":
            GSE_id = item.text
    
    # Check if the GSE ID was not found
    if GSE_id is None:
        print("Error retrieving GSE id\n")
        return None

    return GSE_id

# Download the information of an article with the given ID in a file of SOFT format
def download_soft(GSE_id):
    url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
    params = {
        "acc": str(GSE_id).strip(),
        "targ": "self",
        "form": "text",
        "view": "full"
    }

    response = requests.get(url, params)
    if response.status_code != 200:
        print(f"Failed to download data for article with id: {GSE_id}")
        return None

    filepath = f"{GSE_id}_data_temp.soft"
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(response.content.decode("utf-8"))
    return filepath


def parse_soft_file(filepath, output_json="geo_datasets.json"):
    if filepath is None:
        return None
    # Prepare empty local values
    title = ""
    exp_type = ""
    summary = ""
    design = ""
    organisms = []

    with open(filepath, encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line.startswith("!Series_title ="):
                title = line.replace("!Series_title = ", "")
            elif line.startswith("!Series_type ="):
                exp_type = line.replace("!Series_type = ", "")
            elif line.startswith("!Series_summary ="):
                summary = line.replace("!Series_summary = ", "")
            elif line.startswith("!Series_overall_design ="):
                design = line.replace("!Series_overall_design = ", "")
            elif line.startswith("!Series_sample_organism ="):
                organisms.append(line.replace("!Series_sample_organism = ", ""))

    # Join multiple organisms with "; "
    organism_str = ", ".join(organisms)

    # Try to load existing JSON or create new one
    try:
        with open(output_json, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        existing = {
            "titles": [],
            "types": [],
            "summaries": [],
            "organisms": [],
            "designs": []
        }

    # Append to JSON structure
    existing["titles"].append(title)
    existing["types"].append(exp_type)
    existing["summaries"].append(summary)
    existing["organisms"].append(organism_str)
    existing["designs"].append(design)

    # Write to file
    write_data(output_json, existing)

def delete_soft_files():
    for file in glob.glob("*_data_temp.soft"):
        os.remove(file)


def tf_idf_clustering(pmids, true_k):
    titles = load_data("geo_datasets.json")["titles"]
    types = load_data("geo_datasets.json")["types"]
    summaries = load_data("geo_datasets.json")["summaries"]
    organisms = load_data("geo_datasets.json")["organisms"]
    designs = load_data("geo_datasets.json")["designs"]

    combined_texts = []
    for i in range(len(pmids)):
        combined = f"{titles[i]} {types[i]} {summaries[i]} {organisms[i]} {designs[i]}"
        combined = combined.translate(str.maketrans("", "", string.punctuation))
        combined_texts.append(combined)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        max_features=100,
        max_df=0.8,
        min_df=2 ,
        ngram_range= (1, 3), stop_words="english"
    )

    vectors = vectorizer.fit_transform(combined_texts)
    feature_names = vectorizer.get_feature_names_out()

    dense = vectors.todense()
    denselist = dense.tolist()

    all_keywords = []

    for text in denselist:
        x = 0
        keywords = []
        for word in text:
            if word > 0:
                keywords.append(feature_names[x])
            x += 1
        all_keywords.append(keywords)

    # Clustering the data
    model = KMeans(n_clusters=true_k, init="k-means++", max_iter=100, n_init=1)

    model.fit(vectors)

    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()

    with open("results.txt", "w", encoding="utf-8") as file:
        for i in range(true_k):
            file.write(f"Cluster {i}")
            file.write("\n")
            for ind in order_centroids[i, :10]:
                file.write(" %s" % terms[ind],)
                file.write("\n")
            file.write("\n")
            file.write("\n")

        
    # Data visualization
    kmean_indices = model.fit_predict(vectors)

    pca = PCA(n_components=2)
    scatter_plot_points = pca.fit_transform(vectors.toarray())

    colors = ["r", "b", "c", "y", "m", "orange"]

    x_axis = [o[0] for o in scatter_plot_points]
    y_axis = [o[1] for o in scatter_plot_points]

    fig, ax = plt.subplots(figsize=(10, 10))

    ax.scatter(x_axis, y_axis, c=[colors[d] for d in kmean_indices])

    texts = []
    for i, label in enumerate(pmids):
        texts.append(ax.text(x_axis[i], y_axis[i], label, fontsize=8))

    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray'))

    plt.savefig("trc.png")
