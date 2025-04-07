# PubTrends
PubTrends: Data Insights for Enhanced Paper Relevance

# Features
- Input a list of PMIDs through the web interface
- Visualize the clustered data after extracting it

# Prerequisites
- Python 3.x
- Pip installed
- Additional python packages

# Installation
1\) Clone the repository using the following command:
- git clone https://github.com/s1koO/PubTrends.git

2\) Navigate to the project directory.

3\) Install the aditional packages using the following command:
- **pip install flask requests scikit-learn adjustText matplotlib**

# Usage
1\) Start the program using the following command:
- python main.py

This will start a flask application.

2\) Open a web browser and go to the following link:
- http://127.0.0.1:5000

3\) Write the PMIDs and click on "Visualize Data". You can find in the project directory a file named **PMIDs_list.txt**, which contains an input example consisting of a list with 90 PMIDs.

4\) Wait for the results (this may take a few minutes due to the time it takes to extract the data from the GEO database).

5\) The image with the clustered data visualization will appear on the web page.

# Additional information
After the program is done working and you see the image on the web page, you will find in the project directory the generated image, clusters.txt and articles_data.json.
- **clusters.txt** : contains the clusters formed after the data processing.
- **articles_data.json** : contains the data in json format from all the given articles.
