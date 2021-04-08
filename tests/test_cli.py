import csv
from click.testing import CliRunner
from dorchester.cli import cli


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_plot(source, feature_collection, tmpdir):
    dest = tmpdir / "output.csv"
    population = sum(f.properties["population"] for f in feature_collection.features)
    tolerance = 4  # rounding
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["plot", str(source), str(dest), "--key", "population"]
        )

        assert result.exit_code == 0
        assert dest.exists()

        points = list(csv.DictReader(dest.open()))

        assert abs(len(points) - population) < tolerance
