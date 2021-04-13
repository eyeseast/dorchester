import csv
from click.testing import CliRunner
from dorchester.cli import cli


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_plot(tmpdir, source, feature_collection):
    dest = tmpdir / "output.csv"
    errors = tmpdir / "output.errors.csv"
    population = sum(f.properties["population"] for f in feature_collection.features)
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["plot", str(source), str(dest), "--key", "population"]
        )

        assert result.exit_code == 0
        assert dest.exists()
        assert errors.exists()

        points = list(csv.DictReader(dest.open()))
        offset = sum(int(row["offset"]) for row in csv.DictReader(errors.open()))

        assert (len(points) - offset) == population


def test_no_zeroes(tmpdir, source):
    dest = tmpdir / "output.csv"
    errors = tmpdir / "output.errors.csv"
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["plot", str(source), str(dest), "--key", "population"]
        )

        assert result.exit_code == 0
        assert dest.exists()
        assert errors.exists()

        offsets = [int(row["offset"]) for row in csv.DictReader(errors.open())]
        zeroes = [i for i in offsets if i == 0]

        assert len(zeroes) == 0
