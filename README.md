# dev server
docker pull yangwanjun/scrapy:1.6.0
# 市区町村データ
scrapy crawl boundary_city
# 大字町丁目データ
scrapy crawl boundary_chome
# 駅データ
scrapy crawl station -a username=*** -a password=***
