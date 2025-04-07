from flask import Flask, request, render_template_string, send_file
from task import *

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PMID Cluster Visualizer</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding: 2rem;">
    <h1>PMID Cluster Visualizer</h1>
    <form method="POST" action="/" enctype="application/x-www-form-urlencoded">
        <textarea name="pmids" rows="6" cols="50" placeholder="Enter PMIDs separated by commas or spaces"></textarea><br><br>
        <button type="submit">Generate Cluster</button>
    </form>
    {% if image_ready %}
        <h2>Result:</h2>
        <img src="{{ url_for('serve_image') }}" alt="Cluster Image">
    {% endif %}
</body>
</html>
'''

@app.route('/trc.png')
def serve_image():
    return send_file('trc.png', mimetype='image/png')

@app.route("/", methods=["GET", "POST"])
def index():
    image_ready = False
    if request.method == "POST":
        pmids_raw = request.form.get("pmids", "")
        pmids = [p.strip() for p in pmids_raw.replace(",", " ").split() if p.strip()]

        if pmids:
            clear_data()
            collected_pmids = []
            for pmid in pmids:
                if pmid in collected_pmids:
                    continue
                geo_id = get_geo_id(pmid)
                if geo_id:
                    gse_id = get_GSE_id(geo_id)
                    if gse_id:
                        soft_path = download_soft(gse_id)
                        parse_soft_file(soft_path)
                        collected_pmids.append(pmid)

            delete_soft_files()
            nr_clusters = determine_clusters(len(collected_pmids))
            tf_idf_clustering(collected_pmids, true_k=nr_clusters)
            image_ready = True

    return render_template_string(HTML_TEMPLATE, image_ready=image_ready)

def determine_clusters(num_pmids):
    if num_pmids == 1:
        return 1
    elif num_pmids <= 6:
        return 2
    elif num_pmids <= 18:
        return 3
    else:
        return 6

if __name__ == "__main__":
    app.run(debug=True)
