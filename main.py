from flask import Flask, request, send_file, jsonify, render_template_string
import os
from task import get_geo_id, get_GSE_id, download_soft, parse_soft_file, delete_soft_files, tf_idf_clustering

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PMID Clustering</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding: 2rem;">
    <h1>PMID Cluster Visualizer</h1>
    <form method="POST" action="/" enctype="application/x-www-form-urlencoded">
        <textarea name="pmids" rows="6" cols="50" placeholder="Enter PMIDs separated by commas or spaces"></textarea><br><br>
        <button type="submit">Generate Cluster</button>
    </form>
    {% if image %}
        <h2>Result:</h2>
        <img src="/image" alt="Cluster Image">
    {% endif %}
</body>
</html>
'''

@app.route("/cluster", methods=["POST"])
def cluster():
    try:
        pmids = request.json.get("pmids", [])
        if not pmids:
            return jsonify({"error": "No PMIDs provided"}), 400

        collected_pmids = []

        for pmid in pmids:
            geo_id = get_geo_id(pmid)
            if not geo_id:
                continue
            gse_id = get_GSE_id(geo_id)
            if not gse_id:
                continue
            soft_path = download_soft(gse_id)
            parse_soft_file(soft_path)
            collected_pmids.append(pmid)

        delete_soft_files()

        tf_idf_clustering(collected_pmids)

        return send_file("trc.png", mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/image")
def image():
    return send_file("trc.png", mimetype='image/png')

@app.route("/", methods=["GET", "POST"])
def index():
    image_ready = False
    if request.method == "POST":
        pmids_raw = request.form.get("pmids", "")
        pmids = [p.strip() for p in pmids_raw.replace(",", " ").split() if p.strip()]

        collected_pmids = []
        for pmid in pmids:
            geo_id = get_geo_id(pmid)
            if not geo_id:
                continue
            gse_id = get_GSE_id(geo_id)
            if not gse_id:
                continue
            soft_path = download_soft(gse_id)
            parse_soft_file(soft_path)
            collected_pmids.append(pmid)

        delete_soft_files()

        nr_clusters = 6
        if len(collected_pmids) == 1:
            nr_clusters = 1
        elif len(collected_pmids) <= 6:
            nr_clusters = 2
        elif len(collected_pmids) <= 18:
            nr_clusters = 3

        tf_idf_clustering(collected_pmids, true_k=nr_clusters)
        os.remove("geo_datasets.json")
        image_ready = True

    return render_template_string(HTML_TEMPLATE, image=image_ready)

if __name__ == "__main__":
    app.run(debug=True)
