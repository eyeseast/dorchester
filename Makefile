# download census data for massachusetts
# filter to suffolk county
# run a population build

tests/data/zip/tabblock2010_%_pophu.zip:
	mkdir -p $(dir $@)
	wget -O $@ "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/$(notdir $@)"

tests/data/shp/tabblock2010_%_pophu.shp: tests/data/zip/tabblock2010_%_pophu.zip
	mkdir -p $(dir $@)
	unzip -d tests/data/shp $^

tests/data/suffolk.geojson: tests/data/shp/tabblock2010_25_pophu.shp
	fio cat $^ | fio filter "f.properties.COUNTYFP10 == '025'" | fio collect > $@

tests/data/suffolk.csv: tests/data/suffolk.geojson
	time dorchester plot $^ $@ --key POP10 --progress

profile: tests/data/suffolk.geojson
	python -m cProfile -o tests/data/suffolk.profile -m dorchester.cli $^ /tmp/suffolk.csv --key POP10 --progress

null: tests/data/suffolk.geojson
	time dorchester plot $^ /dev/null --key POP10 --progress --format null

.PHONY: profile null
