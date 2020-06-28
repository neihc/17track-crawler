import json
import click
from src.services.crawl_17track import Crawl17Track


@click.command()
@click.option(
    '--input_path',
    prompt='File input',
    help='A txt file, one tracking per line',
)
@click.option(
    '--output_path', prompt='File output', help='An output file path'
)
def get_trackings(input_path, output_path):
    inf = open(input_path, "r")
    ouf = open(output_path, "w")

    tracking_numbers = inf.readlines()
    crawl_17track_service = Crawl17Track()
    tracking_results = crawl_17track_service.get_all_trackings(
        tracking_numbers
    )

    tracking_results_dict = [t.to_dict() for t in tracking_results]
    tracking_results_json = json.dumps(tracking_results_dict)

    ouf.write(tracking_results_json)

    crawl_17track_service.terminate_driver()
    inf.close()
    ouf.close()
