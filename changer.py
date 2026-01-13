f = open('Список-КМ.csv', 'r', encoding='utf-8')
lines_list = f.readlines()
res = open('result.cql', 'w', encoding='utf-8')
for i, line in enumerate(lines_list):
    line = line.strip()
    res.write(f'{line},\n')
res.close()
f.close()