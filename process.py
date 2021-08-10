import os.path
import requests
from cloudnetpy.categorize import generate_categorize
from cloudnetpy.products import generate_classification
from cloudnetpy.plotting import generate_figure

TEST_CASES = {
    'munich': ('2021-05-16', '2021-05-05', '2021-05-08'),
    'hyytiala': ('2021-05-09', '2021-05-10'),
    'palaiseau': ('2021-03-05', ),
    'granada': ('2021-05-11', '2021-05-07'),
    'norunda': ('2021-03-05', ),
    'bucharest': ('2021-03-05', )
}

URL = 'https://cloudnet.fmi.fi/api/'


def _download_raw_file(site: str, date: str, product: str = None) -> str:
    payload = {'site': site, 'date': date}
    if product is not None:
        payload['product'] = product
        url = f'{URL}files'
    else:
        url = f'{URL}model-files'
    metadata = requests.get(url, payload).json()
    assert len(metadata) <= 1
    if not metadata:
        raise RuntimeError
    filename = metadata[0]['filename']
    link = metadata[0]['downloadUrl']
    _get(link, filename)
    return filename


def _download_image(site: str, date: str) -> None:
    payload = {'site': site, 'date': date, 'product': 'classification',
               'variable[]': 'classification-target_classification'}
    url = f'{URL}visualizations'
    metadata = requests.get(url, payload).json()
    assert len(metadata) == 1
    s3key = metadata[0]["visualizations"][0]["s3key"]
    filename = f'images/{date.replace("-", "")}_{site}_classification.png'
    link = f'{URL}download/image/{s3key}'
    _get(link, filename)


def _get(link: str, filename: str) -> None:
    if not os.path.isfile(filename):
        print(f"downloading {filename} ...")
        res = requests.get(link)
        with open(filename, 'wb') as f:
            f.write(res.content)
    else:
        print(f"already downloaded: {filename}")


def main():
    for site, dates in TEST_CASES.items():
        input_files = {}
        for date in dates:
            input_files['model'] = _download_raw_file(site, date)
            for file_type in ('radar', 'lidar'):
                input_files[file_type] = _download_raw_file(site, date, file_type)
            try:
                input_files['mwr'] = _download_raw_file(site, date, 'mwr')
            except RuntimeError:
                input_files['mwr'] = _download_raw_file(site, date, 'radar')
            _download_image(site, date)

            generate_categorize(input_files, 'categorize.nc')
            generate_classification('categorize.nc', 'classification.nc')
            generate_figure('classification.nc',
                            ['target_classification'],
                            show=False,
                            image_name=f'images/{date.replace("-", "")}_{site}_classification_new')


if __name__ == "__main__":
    main()
