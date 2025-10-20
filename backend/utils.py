import yaml
import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

def load_yaml_from_url(url):
    """
    Функция загрузки YAML по URL
    """
    validate_url = URLValidator()
    try:
        validate_url(url)
    except ValidationError as e:
        raise ValueError(f'Invalid URL: {e}')
    
    response = requests.get(url)
    response.raise_for_status()
    return yaml.safe_load(response.content)

def load_yaml_from_file(file_path):
    """
    Функция загрузки YAML из файла
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)