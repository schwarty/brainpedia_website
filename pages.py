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


memory = Memory(os.path.join(tempfile.gettempdir(), 'cache'))
CWD = os.path.dirname(os.path.abspath(__file__))

get_template = partial(os.path.join, CWD, 'templates')
BOOTSTRAP_DIR = os.path.join(CWD, 'bootstrap-3.3.4-dist')
DATA_DIR = os.path.join(CWD, 'data')
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
    if not os.path.exists(os.path.join(build_dir, 'default.css')):
        shutil.copyfile(os.path.join(CWD, 'css', 'default.css'),
                        os.path.join(build_dir, 'default.css'))


def build(build_dir, images_dir, reset=True, n_jobs=1):
    init_build(build_dir, reset)
    if reset:
        generate_thumbnails.clear()
    large_thumbnails = generate_thumbnails(build_dir, images_dir,
                                           n_jobs=n_jobs)
    small_thumbnails = generate_thumbnails(build_dir, images_dir,
                                           cut_coords=1, n_jobs=n_jobs)
    study_thumbnails = get_study_thumbnails(small_thumbnails)
    print study_thumbnails
    home_page(build_dir, study_thumbnails)


def home_page(build_dir, thumbnails):
    template = tempita.HTMLTemplate.from_filename(get_template('home.html'))
    html = template.substitute(text='lala', thumbnails=thumbnails)

    with open(os.path.join(build_dir, 'home.html'), 'wb') as f:
        f.write(html)


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


def get_study_thumbnails(thumbnails):
    study_thumbnails = {}
    for thumb in thumbnails:
        study_thumbnails.setdefault(thumb[0], thumbnails[thumb])
    return study_thumbnails


if __name__ == '__main__':
    IMAGES_DIR = '/lotta/new_brainpedia/group_stats2'
    build(BUILD_DIR, IMAGES_DIR, reset=False, n_jobs=-1)
