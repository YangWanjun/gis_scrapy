# dev server
```
docker pull yangwanjun/scrapy:1.6.0
```
# 市区町村データ
```
scrapy crawl boundary_city -s LOG_FILE=output/boundary_city.log
```
# 大字町丁目データ
```
scrapy crawl boundary_chome -s LOG_FILE=output/boundary_chome.log
```
# 駅データ
※ settings.pyのITEM_PIPELINESを有効にしてください。
```
scrapy crawl station -a username=*** -a password=***
```
# 郵便番号
※ 先に上記のboundary_cityを実行する必要がある<br/>
```
scrapy crawl postcode -s LOG_FILE=output/postcode.log
```
