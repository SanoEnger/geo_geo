import requests
import json
from datetime import datetime

def test_system():
    """Тестирование исправленной системы"""
    
    print("🚀 Тестирование исправленной системы Geo Photo Analyzer...\n")
    
    base_url = "http://localhost:8000"
    results = {}
    
    # 1. Проверка API Gateway
    print("1. 🌐 Проверка API Gateway...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ API Gateway работает")
            results['api_gateway'] = 'success'
        else:
            print(f"   ❌ API Gateway: {response.status_code}")
            results['api_gateway'] = 'failed'
    except Exception as e:
        print(f"   ❌ API Gateway: {e}")
        results['api_gateway'] = 'failed'
    
    # 2. Проверка здоровья сервисов через Gateway
    print("\n2. 📊 Проверка здоровья сервисов через Gateway...")
    services = ['auth', 'cv_processing', 'photo_upload', 'geocoding']
    
    for service in services:
        try:
            response = requests.get(f"{base_url}/{service}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {service}: {data.get('status', 'healthy')}")
                results[service] = 'success'
            else:
                print(f"   ❌ {service}: {response.status_code}")
                results[service] = 'failed'
        except Exception as e:
            print(f"   ❌ {service}: {e}")
            results[service] = 'failed'
    
    # 3. Проверка корневых endpoints
    print("\n3. 🔍 Проверка корневых endpoints сервисов...")
    for service in services:
        try:
            response = requests.get(f"{base_url}/{service}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {service}: {data.get('message', 'работает')}")
            else:
                print(f"   ⚠️ {service}: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ {service}: {e}")
    
    # 4. Итоги
    print("\n" + "="*50)
    print("📋 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    success_count = sum(1 for result in results.values() if result == 'success')
    total_count = len(results)
    
    print(f"Общий статус: {'SUCCESS' if success_count == total_count else 'PARTIAL'}")
    print(f"Проверено сервисов: {total_count}")
    print(f"Успешных: {success_count}")
    
    if success_count == total_count:
        print("🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ В СИСТЕМЕ")
    
    # Сохраняем результаты
    with open('test_results_fixed.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total': total_count,
                'success': success_count,
                'status': 'success' if success_count == total_count else 'partial'
            }
        }, f, indent=2, ensure_ascii=False)
    
    print("📄 Результаты сохранены в test_results_fixed.json")

if __name__ == "__main__":
    test_system()