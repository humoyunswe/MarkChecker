# Модуль для работы с API марок

Этот модуль предоставляет функции для получения информации о марках из API edo.markirovka.kz.

## Основные функции

### `get_marks_info(bin_number, codes, token)`
Основная функция для получения информации о марках.

**Параметры:**
- `bin_number` (str): БИН номер
- `codes` (List[str]): Список кодов марок
- `token` (str): Bearer токен для авторизации

**Возвращает:**
- Dict: Ответ от API с информацией о марках

**Пример использования:**
```python
from checker.marks import get_marks_info

result = get_marks_info(
    bin_number="850702450693",
    codes=["010463000218039221ucbQbWrD3sJc7"],
    token="your_bearer_token_here"
)
print(result)
```

### `parse_curl_data(curl_command)`
Извлекает данные из curl команды.

**Параметры:**
- `curl_command` (str): Строка с curl командой

**Возвращает:**
- Dict: Словарь с извлеченными данными (token, bin, codes)

**Пример использования:**
```python
from checker.marks import parse_curl_data

curl_command = '''curl --request POST \\
  --url https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km \\
  --header 'Authorization: Bearer YOUR_TOKEN' \\
  --header 'Content-Type: application/json' \\
  --data '{
  "bin": "850702450693",
  "codes": ["010463000218039221ucbQbWrD3sJc7"]
}' '''

parsed_data = parse_curl_data(curl_command)
print(f"БИН: {parsed_data['bin']}")
print(f"Коды: {parsed_data['codes']}")
print(f"Токен: {parsed_data['token']}")
```

### `get_marks_from_curl(curl_command)`
Получает информацию о марках напрямую из curl команды.

**Параметры:**
- `curl_command` (str): Строка с curl командой

**Возвращает:**
- Dict: Ответ от API

**Пример использования:**
```python
from checker.marks import get_marks_from_curl

curl_command = '''curl --request POST \\
  --url https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km \\
  --header 'Authorization: Bearer YOUR_TOKEN' \\
  --header 'Content-Type: application/json' \\
  --data '{
  "bin": "850702450693",
  "codes": ["010463000218039221ucbQbWrD3sJc7"]
}' '''

result = get_marks_from_curl(curl_command)
print(result)
```

### `validate_token(token)`
Проверяет валидность токена.

**Параметры:**
- `token` (str): Bearer токен для проверки

**Возвращает:**
- bool: True если токен валиден, False в противном случае

**Пример использования:**
```python
from checker.marks import validate_token

is_valid = validate_token("your_bearer_token_here")
print(f"Токен валиден: {is_valid}")
```

### `get_marks_for_django_view(bin_number, codes, token)`
Функция для использования в Django views.

**Параметры:**
- `bin_number` (str): БИН номер
- `codes` (List[str]): Список кодов марок
- `token` (str): Bearer токен

**Возвращает:**
- Dict: Словарь с результатом запроса и статусом

**Пример использования:**
```python
from checker.marks import get_marks_for_django_view

result = get_marks_for_django_view(
    bin_number="850702450693",
    codes=["010463000218039221ucbQbWrD3sJc7"],
    token="your_bearer_token_here"
)

if result['success']:
    print("Успешно:", result['data'])
else:
    print("Ошибка:", result['error'])
```

## Тестирование

Для тестирования модуля запустите:

```bash
python test_marks.py
```

Этот скрипт продемонстрирует:
1. Извлечение данных из curl команды
2. Проверку валидности токена
3. Выполнение запроса к API
4. Обработку ошибок

## Интеграция с Django

Для интеграции с Django views используйте функцию `get_marks_for_django_view`:

```python
from checker.marks import get_marks_for_django_view

def your_django_view(request):
    if request.method == 'POST':
        bin_number = request.POST.get('bin')
        codes = request.POST.getlist('codes')
        token = request.POST.get('token')
        
        result = get_marks_for_django_view(bin_number, codes, token)
        
        if result['success']:
            # Обработка успешного ответа
            return JsonResponse(result['data'])
        else:
            # Обработка ошибки
            return JsonResponse({'error': result['error']}, status=400)
```

## Обработка ошибок

Модуль обрабатывает следующие типы ошибок:
- `requests.RequestException`: Ошибки HTTP запросов
- `ValueError`: Неверные параметры или ошибки парсинга JSON
- `json.JSONDecodeError`: Ошибки парсинга JSON ответа

## Требования

- Python 3.6+
- requests
- Django (для интеграции с Django views)

## Безопасность

- Токены должны храниться в безопасном месте
- Не передавайте токены в открытом виде
- Используйте HTTPS для всех запросов
- Регулярно обновляйте токены 