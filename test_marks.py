#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации работы с API марок
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from checker.marks import (
    get_marks_info, 
    parse_curl_data, 
    get_marks_from_curl,
    validate_token,
    extract_token_from_curl
)

def main():
    print("=== Тест API марок ===\n")
    
    # Ваш curl запрос
    curl_command = '''curl --request POST \\
  --url https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km \\
  --header 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJoaVZzazdUN2s2d09adG9JOHpQdjBsZ1EwNmE4XzV3aWlUQVBUNmd5QjI4In0.eyJqdGkiOiI0NmZlODhlZS1kZDhhLTQ3ZmUtOGFiYy1kY2MyN2EyNjU3ZTkiLCJleHAiOjE3NTM4NTQ3NTEsIm5iZiI6MCwiaWF0IjoxNzUzODUxMTUxLCJpc3MiOiJodHRwczovL2lkcC5pc21ldC5rei9hdXRoL3JlYWxtcy9vY3AiLCJhdWQiOiJlZG8ubWFya2lyb3ZrYS5reiIsInN1YiI6IjE2NDgwY2QzLTQ0M2YtNDEyYS05NWJhLTlkOWFmNzhkMTA4NCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImVkby5tYXJraXJvdmthLmt6IiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiMDMyNTA0ZWUtZGIxOS00ZTZjLTgyNmYtODYzMTVjYzM0MThjIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL25zcHQuaXNtZXQua3oiLCJodHRwczovL2Vkby5tYXJraXJvdmthLmt6Il0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInVzZXJfbmFtZSI6ImFyYWlseW0uc2hhcmlwb3ZhQGRpZ2l0YWxlY29ub215Lmt6IiwibmFtZSI6IkFyYWlseW0gU2hhcmlwb3ZhIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYXJhaWx5bS5zaGFyaXBvdmFAZGlnaXRhbGVjb25vbXkua3oiLCJnaXZlbl9uYW1lIjoiQXJhaWx5bSIsImZhbWlseV9uYW1lIjoiU2hhcmlwb3ZhIiwiZW1haWwiOiJhcmFpbHltLnNoYXJpcG92YUBkaWdpdGFsZWNvbm9teS5reiJ9.UjeLbmWbC0nzJ51I-vvDWQqwmORJ2QZD_yBmbpMYl-zI1yoWQJ2toxmeWWVKvwmO1Q9EzKDYRR_yTtfK6QltpZZ9CAB8XgzI4zJzELMHiU1oOueXy2k8T2DwoPaGJ2jXY5FLadta5I4VSoRU00MVdOFq-9f8e-2tY0nh185h8bzIJTRoObAdgmvZqDXI9Qba_rofn7nCOE7DWmoOp1wdY7rddKC00skwGIqQ0QrWoKmxeSJUKfoSmjmdcYcA6A8c3RTJMcBSZSYi6LsSEjqozeM0AHlrkW60MeEcMotBeymRBIm9MlCyvpfPOyGPXNlVVCjpRjyUiagH1dO-k4DKgA' \\
  --header 'Content-Type: application/json' \\
  --data '{
  "bin": "850702450693",
  "codes": [
"010463000218039221ucbQbWrD3sJc7"
  ]
}'''
    
    print("1. Извлечение данных из curl команды:")
    print("-" * 50)
    
    parsed_data = parse_curl_data(curl_command)
    print(f"БИН: {parsed_data['bin']}")
    print(f"Коды марок: {parsed_data['codes']}")
    print(f"Токен найден: {'Да' if parsed_data['token'] else 'Нет'}")
    
    if parsed_data['token']:
        print(f"Длина токена: {len(parsed_data['token'])} символов")
        
        print("\n2. Проверка валидности токена:")
        print("-" * 50)
        
        is_valid = validate_token(parsed_data['token'])
        print(f"Токен валиден: {'Да' if is_valid else 'Нет'}")
        
        if is_valid:
            print("\n3. Выполнение запроса к API:")
            print("-" * 50)
            
            try:
                result = get_marks_info(
                    bin_number=parsed_data['bin'],
                    codes=parsed_data['codes'],
                    token=parsed_data['token']
                )
                
                print("✅ Успешный ответ от API:")
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            except Exception as e:
                print(f"❌ Ошибка при запросе к API: {e}")
        else:
            print("❌ Токен невалиден, запрос к API не выполнен")
    else:
        print("❌ Токен не найден в curl команде")
    
    print("\n4. Альтернативный способ - прямое использование:")
    print("-" * 50)
    
    # Прямое использование с вашими данными
    try:
        result = get_marks_info(
            bin_number="850702450693",
            codes=["010463000218039221ucbQbWrD3sJc7"],
            token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJoaVZzazdUN2s2d09adG9JOHpQdjBsZ1EwNmE4XzV3aWlUQVBUNmd5QjI4In0.eyJqdGkiOiI0NmZlODhlZS1kZDhhLTQ3ZmUtOGFiYy1kY2MyN2EyNjU3ZTkiLCJleHAiOjE3NTM4NTQ3NTEsIm5iZiI6MCwiaWF0IjoxNzUzODUxMTUxLCJpc3MiOiJodHRwczovL2lkcC5pc21ldC5rei9hdXRoL3JlYWxtcy9vY3AiLCJhdWQiOiJlZG8ubWFya2lyb3ZrYS5reiIsInN1YiI6IjE2NDgwY2QzLTQ0M2YtNDEyYS05NWJhLTlkOWFmNzhkMTA4NCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImVkby5tYXJraXJvdmthLmt6IiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiMDMyNTA0ZWUtZGIxOS00ZTZjLTgyNmYtODYzMTVjYzM0MThjIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL25zcHQuaXNtZXQua3oiLCJodHRwczovL2Vkby5tYXJraXJvdmthLmt6Il0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInVzZXJfbmFtZSI6ImFyYWlseW0uc2hhcmlwb3ZhQGRpZ2l0YWxlY29ub215Lmt6IiwibmFtZSI6IkFyYWlseW0gU2hhcmlwb3ZhIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYXJhaWx5bS5zaGFyaXBvdmFAZGlnaXRhbGVjb25vbXkua3oiLCJnaXZlbl9uYW1lIjoiQXJhaWx5bSIsImZhbWlseV9uYW1lIjoiU2hhcmlwb3ZhIiwiZW1haWwiOiJhcmFpbHltLnNoYXJpcG92YUBkaWdpdGFsZWNvbm9teS5reiJ9.UjeLbmWbC0nzJ51I-vvDWQqwmORJ2QZD_yBmbpMYl-zI1yoWQJ2toxmeWWVKvwmO1Q9EzKDYRR_yTtfK6QltpZZ9CAB8XgzI4zJzELMHiU1oOueXy2k8T2DwoPaGJ2jXY5FLadta5I4VSoRU00MVdOFq-9f8e-2tY0nh185h8bzIJTRoObAdgmvZqDXI9Qba_rofn7nCOE7DWmoOp1wdY7rddKC00skwGIqQ0QrWoKmxeSJUKfoSmjmdcYcA6A8c3RTJMcBSZSYi6LsSEjqozeM0AHlrkW60MeEcMotBeymRBIm9MlCyvpfPOyGPXNlVVCjpRjyUiagH1dO-k4DKgA"
        )
        
        print("✅ Успешный ответ от API:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Ошибка при запросе к API: {e}")

if __name__ == "__main__":
    main() 