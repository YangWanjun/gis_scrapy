# dev server
docker pull yangwanjun/scrapy:1.6.0
# 市区町村データ
scrapy crawl boundary_city
# 駅データ
scrapy crawl station -a username=*** -a password=***
