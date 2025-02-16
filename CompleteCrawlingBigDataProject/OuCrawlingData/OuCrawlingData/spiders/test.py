file_path = "D:/CompleteCrawlingBigDataProject/OuCrawlingData/ou_data.json"

with open(file_path, "r", encoding="utf-8") as f:
    for i in range(10000):
        print(f.readline().strip())
