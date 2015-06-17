import os
import glob
import shutil
import tempfile
from functools import partial

import nibabel as nb
import numpy as np
import tempita

from nilearn.plotting import plot_stat_map
from joblib import Parallel, delayed, Memory
from utils import prettify_label


memory = Memory(os.path.join(tempfile.gettempdir(), 'cache'))
CWD = os.path.dirname(os.path.abspath(__file__))

get_template = partial(os.path.join, CWD, 'templates')
BOOTSTRAP_DIR = os.path.join(CWD, 'bootstrap-3.3.4-dist')
DATA_DIR = os.path.join(CWD, 'data')
CSS_DIR = os.path.join(CWD, 'css')
BUILD_DIR = os.path.join(tempfile.gettempdir(), 'brainpedia')


def init_build(build_dir, reset):
    if os.path.exists(build_dir) and reset:
        shutil.rmtree(build_dir)
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    if not os.path.exists(os.path.join(build_dir, 'thumbnails')):
        os.makedirs(os.path.join(build_dir, 'thumbnails'))
    if not os.path.exists(os.path.join(build_dir, 'bootstrap')):
        shutil.copytree(BOOTSTRAP_DIR,
                        os.path.join(build_dir, 'bootstrap'))
    if not os.path.exists(os.path.join(build_dir, 'data')):
        shutil.copytree(DATA_DIR, os.path.join(build_dir, 'data'))
    if not os.path.exists(os.path.join(build_dir, 'css')):
        shutil.copytree(CSS_DIR, os.path.join(build_dir, 'css'))


def build(build_dir, images_dir, ignore=None, reset=True, n_jobs=1):
    init_build(build_dir, reset)
    if reset:
        generate_thumbnails.clear()
    # large_thumbnails = generate_thumbnails(build_dir, images_dir,
    #                                       n_jobs=n_jobs)
    thumbnails = generate_thumbnails(build_dir, images_dir,
                                     cut_coords=1, n_jobs=n_jobs)
    thumbnails = get_study_thumbnails(thumbnails, ignore)
    labels = get_studies_labels(thumbnails.keys())

    home_page(build_dir, thumbnails, labels)


def home_page(build_dir, thumbnails, labels):
    template = tempita.HTMLTemplate.from_filename(get_template('home.html'))
    html = template.substitute(thumbnails=thumbnails, labels=labels)

    with open(os.path.join(build_dir, 'home.html'), 'wb') as f:
        f.write(html)


def get_studies_labels(include=None):
    labels = {}
    with open(os.path.join(DATA_DIR, 'labels.csv')) as f:
        text = f.read()
        for line in text.split('\n'):
            if line != '':
                cols = line.split(', ')
                study_id, _ = cols[0].split('_', 1)
                if include is None or study_id in include:
                    new_labels = [prettify_label(l) for l in cols[1:]]
                    labels.setdefault(study_id, set()).update(new_labels)
                else:
                    print 'study %s does not have thumbnails' % study_id
    for label in labels:
        labels[label] = sorted(labels[label])
    return labels


@memory.cache
def generate_thumbnails(build_dir, images_dir, cut_coords=5, n_jobs=1):
    thumbnails = Parallel(n_jobs=n_jobs)(
        delayed(_generate_thumbnail)(build_dir, img, cut_coords)
        for img in glob.glob(os.path.join(images_dir, '*', '*.nii.gz')))
    return dict([(thumb[:3], thumb[-1]) for thumb in thumbnails])


def _generate_thumbnail(build_dir, img, cut_coords):
    threshold = np.percentile(nb.load(img).get_data(), 97)
    display = plot_stat_map(img, threshold=threshold,
                            cut_coords=cut_coords, display_mode='z',
                            annotate=False, colorbar=False,
                            draw_cross=False, black_bg=False)

    study_id = img.split(os.path.sep)[-2]
    task_id, map_id = os.path.split(img)[-1].split('.nii.gz')[0].split('_', 1)
    fname = '%s_%s_%s.png' % (
        img.split(os.path.sep)[-2],
        os.path.split(img)[-1].split('.nii.gz')[0], cut_coords)
    fname = os.path.join(build_dir, 'thumbnails', fname)
    display.savefig(fname, dpi=200)
    return study_id, task_id, map_id, fname


def get_study_thumbnails(thumbnails, ignore=None):
    study_thumbnails = {}
    for thumb in thumbnails:
        if ignore is None or not thumb[0] in ignore:
            study_thumbnails.setdefault(thumb[0], thumbnails[thumb])
    return study_thumbnails


if __name__ == '__main__':
    IMAGES_DIR = '/lotta/new_brainpedia/group_stats2'
    ignore = ['amalric2012mathematicians', 'cauvet2009muslang', ]
    build(BUILD_DIR, IMAGES_DIR, ignore=ignore, reset=True, n_jobs=-1)


"""
    {{for loop, study_id in looper(sorted(labels.keys()))}}
    <div class="media">
      <div class="panel panel-primary">
        <div class="panel-heading">
          <h3 class="panel-title">{{study_id}}</h3>
        </div>
        <div class="panel-body">
          <div class="media-left">
            <a href="#">
              <img class="media-object" src={{thumbnails[study_id]}} alt={{study_id}} height="128" width="128">
            </a>
          </div>
          <div class="media-body">
            {{for label in sorted(labels[study_id])}}
              <span class="label label-default">{{label}}</span>
            {{endfor}}
          </div>
        </div>
      </div>
    </div><!-- /.container -->
    {{endfor}}
"""
