# dev server
docker pull yangwanjun/scrapy:1.6.0
# 市区町村データ
scrapy crawl boundary_city -s LOG_FILE=output/boundary_city.log
# 大字町丁目データ
scrapy crawl boundary_chome -s LOG_FILE=output/boundary_chome.log
# 駅データ
scrapy crawl station -a username=*** -a password=***
# 郵便番号
scrapy crawl postcode -s LOG_FILE=output/postcode.log
