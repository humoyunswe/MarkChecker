import requests
import json
from typing import List, Dict, Optional
from django.conf import settings


def get_marks_info(bin_number: str, codes: List[str], token: Optional[str] = None) -> Dict:
    """
    Получает информацию о марках из API edo.markirovka.kz
    
    Args:
        bin_number (str): БИН номер
        codes (List[str]): Список кодов марок
        token (str, optional): Bearer токен. Если не указан, используется токен из настроек
    
    Returns:
        Dict: Ответ от API с информацией о марках
    
    Raises:
        requests.RequestException: При ошибке HTTP запроса
        ValueError: При неверных параметрах
    """
    
    # URL API
    url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km"
    
    # Используем переданный токен или токен из настроек
    if token is None:
        # Здесь можно добавить получение токена из настроек Django
        # token = getattr(settings, 'EDO_API_TOKEN', None)
        # if token is None:
        #     raise ValueError("Токен не указан и не найден в настройках")
        raise ValueError("Токен должен быть указан")
    
    # Заголовки запроса
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Данные запроса
    data = {
        "bin": bin_number,
        "codes": codes
    }
    
    try:
        # Выполняем POST запрос
        response = requests.post(
            url=url,
            headers=headers,
            json=data,
            timeout=30  # Таймаут 30 секунд
        )
        
        # Проверяем статус ответа
        response.raise_for_status()
        
        # Возвращаем JSON ответ
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Ошибка при запросе к API: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка при парсинге JSON ответа: {str(e)}")


def get_marks_info_simple(bin_number: str, codes: List[str], token: str) -> Dict:
    """
    Упрощенная версия функции для получения информации о марках
    
    Args:
        bin_number (str): БИН номер
        codes (List[str]): Список кодов марок
        token (str): Bearer токен
    
    Returns:
        Dict: Ответ от API
    """
    return get_marks_info(bin_number, codes, token)


def validate_token(token: str) -> bool:
    """
    Проверяет валидность токена, делая тестовый запрос
    
    Args:
        token (str): Bearer токен для проверки
    
    Returns:
        bool: True если токен валиден, False в противном случае
    """
    try:
        # Делаем тестовый запрос с минимальными данными
        test_data = {
            "bin": "000000000000",  # Тестовый БИН
            "codes": ["test_code"]  # Тестовый код
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            url="https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        # Если получаем 401 - токен невалиден
        if response.status_code == 401:
            return False
        
        # Если получаем 400 - токен валиден, но данные неверные (это нормально)
        if response.status_code == 400:
            return True
        
        # Если получаем 200 - токен валиден
        if response.status_code == 200:
            return True
        
        return False
        
    except Exception:
        return False


def extract_token_from_curl(curl_command: str) -> Optional[str]:
    """
    Извлекает токен из curl команды
    
    Args:
        curl_command (str): Строка с curl командой
    
    Returns:
        Optional[str]: Извлеченный токен или None если не найден
    """
    try:
        # Ищем строку с Authorization: Bearer
        lines = curl_command.split('\n')
        for line in lines:
            if 'Authorization: Bearer' in line:
                # Извлекаем токен после 'Bearer '
                token_start = line.find('Bearer ') + 7
                token_end = line.find("'", token_start)
                if token_end == -1:
                    token_end = line.find('"', token_start)
                if token_end == -1:
                    token_end = len(line)
                
                return line[token_start:token_end].strip()
        return None
    except Exception:
        return None


def parse_curl_data(curl_command: str) -> Dict:
    """
    Парсит данные из curl команды
    
    Args:
        curl_command (str): Строка с curl командой
    
    Returns:
        Dict: Словарь с извлеченными данными
    """
    result = {
        'token': None,
        'bin': None,
        'codes': []
    }
    
    try:
        # Извлекаем токен
        result['token'] = extract_token_from_curl(curl_command)
        
        # Ищем данные в --data секции
        if '--data' in curl_command:
            data_start = curl_command.find('--data')
            data_section = curl_command[data_start:]
            
            # Ищем JSON данные
            json_start = data_section.find('{')
            json_end = data_section.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = data_section[json_start:json_end]
                try:
                    data = json.loads(json_str)
                    result['bin'] = data.get('bin')
                    result['codes'] = data.get('codes', [])
                except json.JSONDecodeError:
                    pass
                    
    except Exception:
        pass
    
    return result


def get_marks_from_curl(curl_command: str) -> Dict:
    """
    Получает информацию о марках из curl команды
    
    Args:
        curl_command (str): Строка с curl командой
    
    Returns:
        Dict: Ответ от API с информацией о марках
    
    Raises:
        ValueError: Если не удалось извлечь данные из curl команды
    """
    # Парсим данные из curl команды
    parsed_data = parse_curl_data(curl_command)
    
    if not parsed_data['token']:
        raise ValueError("Не удалось извлечь токен из curl команды")
    
    if not parsed_data['bin']:
        raise ValueError("Не удалось извлечь БИН из curl команды")
    
    if not parsed_data['codes']:
        raise ValueError("Не удалось извлечь коды марок из curl команды")
    
    # Делаем запрос к API
    return get_marks_info(
        bin_number=parsed_data['bin'],
        codes=parsed_data['codes'],
        token=parsed_data['token']
    )


def get_marks_for_django_view(bin_number: str, codes: List[str], token: str) -> Dict:
    """
    Функция для использования в Django views
    
    Args:
        bin_number (str): БИН номер
        codes (List[str]): Список кодов марок
        token (str): Bearer токен
    
    Returns:
        Dict: Словарь с результатом запроса и статусом
    """
    try:
        result = get_marks_info(bin_number, codes, token)
        return {
            'success': True,
            'data': result,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }


# Пример использования:
if __name__ == "__main__":
    # Пример данных
    bin_example = "850702450693"
    codes_example = ["010463000218039221ucbQbWrD3sJc7"]
    token_example = "YOUR_TOKEN_HERE"  # Замените на ваш токен
    
    try:
        result = get_marks_info(bin_example, codes_example, token_example)
        print("Успешный ответ:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # Пример извлечения данных из curl команды
    curl_example = '''
    curl --request POST \
      --url https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km \
      --header 'Authorization: Bearer YOUR_TOKEN_HERE' \
      --header 'Content-Type: application/json' \
      --data '{
      "bin": "850702450693",
      "codes": [
    "010463000218039221ucbQbWrD3sJc7"
      ]
    }'
    '''
    
    parsed_data = parse_curl_data(curl_example)
    print("\nИзвлеченные данные из curl:")
    print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
