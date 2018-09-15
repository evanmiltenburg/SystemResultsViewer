# Stdlib
import json
import os
from collections import defaultdict
from urllib.request import urlretrieve

# Installed
from flask import Flask, request, render_template, redirect, make_response

################################################################################
# Functions to load the data.

def load_system_output(filename):
    "Load system output as a dictionary: imgid: description."
    with open(filename) as f:
        data = json.load(f)
    return {str(image['image_id']): image['caption'] for image in data}


def load_human_data(filename):
    "Load the human descriptions."
    with open(filename) as f:
        data = json.load(f)
    description_index = defaultdict(list)
    for image in data['annotations']:
        key = str(image['image_id'])
        caption = image['caption']
        description_index[key].append(caption)
    return description_index


def load_image_data(filename):
    "Load the image URLs and filenames."
    with open(filename) as f:
        data = json.load(f)
    return {str(image['id']): {'url': image['coco_url'],
                               'filename': image['coco_url'].split('_')[-1]}
            for image in data['images']}


def load_all_systems(system_files):
    "Load system data by images: {imgid: {system: caption, ...}, ...}"
    system_data = {system: load_system_output(filename)
                    for system,filename in system_files.items()}
    system_data_by_images = defaultdict(dict)
    for system, index in system_data.items():
        for image_id, caption in index.items():
            system_data_by_images[image_id][system] = caption
    return system_data_by_images


def download_url(url, folder='./static/COCO-images/'):
    "Download a file to a particular folder."
    filename = url.split('_')[-1]
    local_filename, headers = urlretrieve(url, folder + filename)
    print('Downloaded:', local_filename)
    print('Headers:', headers)

################################################################################
# Loading the data.

system_files = {'Dai et al. 2017': './Data/Systems/Dai-et-al-2017/Val/gan_val2014.json',
                'Liu et al. 2017': './Data/Systems/Liu-et-al-2017/Val/captions_val2014_MAT_results.json',
                'Mun et al. 2017': './Data/Systems/Mun-et-al-2017/Val/captions_val2014_senAttKnn-kCC_results.json',
                'Shetty et al. 2016': './Data/Systems/Shetty-et-al-2016/Val/captions_val2014_r-dep3-frcnn80detP3+3SpatGaussScaleP6grRBFsun397-gaA3cA3-per9.72-b5_results.json',
                'Shetty et al. 2017': './Data/Systems/Shetty-et-al-2017/Val/captions_val2014_MLE-20Wrd-Smth3-randInpFeatMatch-ResnetMean-56k-beamsearch5_results.json',
                'Tavakoli et al. 2017': './Data/Systems/Tavakoli-et-al-2017/Val/captions_val2014_PayingAttention-ICCV2017_results.json',
                'Vinyals et al. 2017': './Data/Systems/Vinyals-et-al-2017/Val/captions_val2014_googlstm_results.json',
                'Wu et al. 2016': './Data/Systems/Wu-et-al-2016/Val/captions_val2014_Attributes_results.json',
                'Zhou et al. 2017': './Data/Systems/Zhou-et-al-2017/Val/captions_val2014_e2e_results.json'}

human_data = load_human_data('./Data/COCO/captions_val2014.json')
image_data = load_image_data('./Data/COCO/captions_val2014.json')
system_data = load_all_systems(system_files)

imgids = list(image_data)
first_id = imgids[0]
max_index = len(imgids) - 1

################################################################################
# Global variables to make search possible.
search        = False
query         = ''
result_ids    = []
before_search = first_id

################################################################################
# Set up app:
app = Flask(__name__)

################################################################################
# Main browsing functionality.

@app.route('/')
def main():
    "Main page redirects to the first item to be annotated."
    page = '/item/' + first_id
    return redirect(page)


@app.route('/item/<imgid>')
def item_page(imgid):
    """
    Serve the item page.
    """
    # Assess whether there is an image before or after the current page.
    current_index = imgids.index(imgid)
    if current_index > 0:
        previous = '/item/' + imgids[current_index -1]
    else:
        previous = None
    if current_index < max_index:
        next = '/item/' + imgids[current_index + 1]
    else:
        next = None
    
    # Get data to display
    human_captions = human_data[imgid]
    system_captions = system_data[imgid]
    image = image_data[imgid]['filename']
    
    # Check if the image exists. If not, download it.
    if not os.path.isfile('./static/COCO-images/' + image):
        print("We need to download the image!")
        url = image_data[imgid]['url']
        download_url(url)
    return render_template('index.html',
                            imgid=imgid,
                            humans=human_captions,
                            systems=system_captions,
                            image='/static/COCO-images/' + image,
                            next_page=next,
                            previous_page=previous,
                            )

################################################################################
# Running the website

if __name__ == '__main__':
    app.debug = True
app.run(threaded=True)
