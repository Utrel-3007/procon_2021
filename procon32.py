import io
import time
import urllib.parse

import click
import requests

import config

URL_DOWNLOAD = config.URL_DOWNLOAD
URL_SUBMIT = config.URL_SUBMIT
TOKEN = config.TOKEN
PROBLEM_NAME = config.PROBLEM_NAME
SOLUTION_NAME = config.SOLUTION_NAME


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--url", envvar="PROCON32_URL", default=URL_DOWNLOAD)
@click.option("--token", envvar="PROCON32_TOKEN", default=f"Bearer {TOKEN}")
@click.option("--wait", type=bool, default=False, help="問題が有効になるまで繰り返し取得します")
@click.option("--interval", type=int, default=5, help="--wait が指定されている場合の問題の取得間隔(秒)")
@click.option(
    "-o", type=click.File(mode="wb"), default=f"{PROBLEM_NAME}", help="取得した問題の出力先"
)
def download(url: str, token: str, wait: bool, interval: int, o: io.BytesIO) -> None:
    endpoint = urllib.parse.urljoin(url, "")
    while True:
        r = requests.get(endpoint, headers={"Authorization": token})
        if r.status_code == 200:
            o.write(r.content)

            f = open(f"{PROBLEM_NAME}", "rb").read().split()
            print(f"HEIGHT : {int(f[3])}")
            print(f"WIDTH  : {int(f[2])}")
            print(f"SELECT : {int(f[5])}")
            return

        click.echo(f"{r.status_code} {r.text.strip()}", err=True)
        if not wait:
            return

        time.sleep(_get_interval(r.status_code, r.text, interval))


@cli.command()
@click.option("--url", envvar="PROCON32_URL", default=URL_SUBMIT)
@click.option("--token", envvar="PROCON32_TOKEN", default=f"Bearer {TOKEN}")
@click.option("-f", type=click.File("r"), default=f"{SOLUTION_NAME}")
def submit(url: str, token: str, f: io.StringIO) -> None:
    endpoint = url
    fi = open(f"{SOLUTION_NAME}", "r")
    fdata = fi.read()
    r = requests.post(endpoint, headers={
                      "Authorization": token, "Content-Type": "text/plain"}, data=fdata)
    if r.status_code == 200:
        click.echo(r.text.strip())
        return
    click.echo(f"{r} {r.status_code} {r.text.strip()}")


def _get_interval(status_code: int, text: str, interval: int) -> int:
    """
    >>> _get_interval(400, "AccessTimeError 30", 5)
    30
    >>> _get_interval(400, "AccessTimeError", 5)
    5
    >>> _get_interval(500, "InternalServerError", 10)
    10
    """
    if status_code != 400:
        return interval
    tokens = text.split(" ")
    if tokens[0] != "AccessTimeError":
        return interval
    if len(tokens) != 2:
        return interval
    return int(tokens[1])


if __name__ == "__main__":
    cli()
