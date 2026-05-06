from json5 import loads, load

with open("test.json", encoding="utf-8") as file:
    root = load(file)
    data = loads(root["data"])
    
print(data)