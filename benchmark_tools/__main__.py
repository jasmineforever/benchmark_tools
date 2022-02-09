import click
from benchmark_tools import benchmark_tool


@click.command()
@click.option('-f', '--file', help='The benchmark client class file', required=True, type=click.Path(exists=True))
def run_benchmark(file):
    benchmark_tool.run(file)


if __name__ == '__main__':
    run_benchmark()
