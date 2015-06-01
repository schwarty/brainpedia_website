import os
import glob
import shutil
import tempfile
from functools import partial

import nibabel as nb
import numpy as np
import tempita

from nilearn.plotting import plot_stat_map
from joblib import Parallel, delayed


cwd = os.path.dirname(os.path.abspath(__file__))

get_template = partial(os.path.join, cwd, 'templates')
bootstrap_dir = os.path.join(cwd, 'bootstrap-3.3.4-dist')
data_dir = os.path.join(cwd, 'data')
build_dir_ = os.path.join(tempfile.gettempdir(), 'brainpedia')


def init_build(build_dir=build_dir_):
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    os.makedirs(os.path.join(build_dir, 'thumbnails'))
    shutil.copytree(bootstrap_dir, os.path.join(build_dir, 'bootstrap'))
    shutil.copytree(data_dir, os.path.join(build_dir, 'data'))
    shutil.copyfile(os.path.join(cwd, 'css', 'default.css'),
                    os.path.join(build_dir, 'default.css'))


def home_page(build_dir=build_dir_):
    template = tempita.HTMLTemplate.from_filename(get_template('home.html'))
    html = template.substitute(text='lala')

    with open(os.path.join(build_dir, 'home.html'), 'wb') as f:
        f.write(html)


def generate_thumbnails(images_dir, build_dir=build_dir_, n_jobs=1):
    Parallel(n_jobs=n_jobs)(
        delayed(_generate_thumbnail)(img, build_dir)
        for img in glob.glob(os.path.join(images_dir, '*', '*.nii.gz')))


def _generate_thumbnail(img, build_dir):
    threshold = np.percentile(nb.load(img).get_data(), 97)
    display = plot_stat_map(img, threshold=threshold,
                            cut_coords=5, display_mode='z',
                            annotate=False, colorbar=False,
                            draw_cross=False, black_bg=True)
    fname = '%s_%s.png' % (
        img.split(os.path.sep)[-2],
        os.path.split(img)[-1].split('.nii.gz')[0])
    fname = os.path.join(build_dir, 'thumbnails', fname)
    display.savefig(fname, dpi=200)


if __name__ == '__main__':
    init_build()
    home_page()
    #generate_thumbnails('/lotta/new_brainpedia/group_stats2', n_jobs=-1)
