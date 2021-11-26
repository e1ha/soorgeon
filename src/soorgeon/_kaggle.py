"""
CLI for downloading Kaggle notebooks for integration testing
"""
from functools import partial
import zipfile
import shutil
from pathlib import PurePosixPath, Path

import click
import jupytext
from kaggle import api


def process_index(index):
    return {PurePosixPath(i['url']).name: _add_partial(i) for i in index}


def _add_partial(d):
    url_data = PurePosixPath(d['data'])
    is_competition = 'c' in url_data.parts
    fn = download_from_competition if is_competition else download_from_dataset

    if is_competition:
        name = url_data.name
    else:
        name = str(PurePosixPath(*url_data.parts[-2:]))

    kwargs = dict(name=name)

    if d.get('files'):
        kwargs['files'] = d['files']

    return {**d, **dict(partial=partial(fn, **kwargs))}


def download_from_competition(name, files=None):
    # FIXME: add support for more than one file
    api.competition_download_cli(name, file_name=files)

    if not files:
        with zipfile.ZipFile(f'{name}.zip', 'r') as file:
            file.extractall('input')
    else:
        Path('input').mkdir()
        shutil.move(files, Path('input', files))


def download_from_dataset(name):
    api.dataset_download_cli(name, unzip=True, path='input')


@click.group()
def cli():
    pass


@cli.command()
@click.argument('kernel_path')
def notebook(kernel_path):
    click.echo('Downloading notebook...')
    name = PurePosixPath(kernel_path).name
    api.kernel_paths_pull_cli(kernel=kernel_path, path=name)

    click.echo('Converting to .py...')
    ipynb = Path(name, f'{name}.ipynb')
    py = Path(name, 'nb.py')
    nb = jupytext.read(ipynb)
    jupytext.write(nb, py, fmt='py:percent')
    ipynb.unlink()


# FIXME: add files arg
@cli.command()
@click.argument('name')
def competition(name):
    download_from_competition(name=name)


@cli.command()
@click.argument('name')
def dataset(name):
    download_from_dataset(name=name)


if __name__ == '__main__':
    cli()
