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

tests/data/suffolk-race.csv: tests/data/suffolk-2010-race.geojson
	time dorchester plot $^ $@ --progress \
	  -k White \
	  -k "Black or African American" \
	  -k "American Indian and Alaska Native" \
	  -k "Asian" \
	  -k "Native Hawaiian and Other Pacific Islander" \
	  -k Other \
	  -k "Two or More Races"

tests/data/suffolk-2010-race.mbtiles: tests/data/suffolk-race.csv
	tippecanoe -zg -o $@ --drop-densest-as-needed --extend-zooms-if-still-dropping $^

profile: tests/data/suffolk-2010-race.geojson
	time python -m cProfile -o tests/data/suffolk.profile -m dorchester.cli $^ /tmp/suffolk.csv \
	  --progress \
	  -k White \
	  -k "Black or African American" \
	  -k "American Indian and Alaska Native" \
	  -k "Asian" \
	  -k "Native Hawaiian and Other Pacific Islander" \
	  -k Other \
	  -k "Two or More Races"

test:
	pytest -n 4 -v

null: tests/data/suffolk.geojson
	time dorchester plot $^ /dev/null --key POP10 --progress --format null

.PHONY: profile null
