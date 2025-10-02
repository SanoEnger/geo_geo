import requests
import json
import time
import os
from datetime import datetime

def test_system():
    """Полное тестирование всей системы"""
    
    base_url = "http://localhost:8000"
    results = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "overall": "PASS"
    }
    
    print("🚀 Начинаем полное тестирование системы Geo Photo Analyzer...")
    
    # 1. Тестирование здоровья сервисов
    print("\n1. 📊 Проверка здоровья сервисов...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        health_data = health_response.json()
        
        for service, status in health_data.get("services", {}).items():
            service_status = status.get("status", "unknown")
            results["services"][service] = service_status
            
            if service_status == "healthy":
                print(f"   ✅ {service}: {service_status}")
            else:
                print(f"   ❌ {service}: {service_status}")
                results["overall"] = "FAIL"
                
    except Exception as e:
        print(f"   ❌ Ошибка проверки здоровья: {e}")
        results["overall"] = "FAIL"
    
    # 2. Тестирование API Gateway
    print("\n2. 🌐 Тестирование API Gateway...")
    try:
        gateway_response = requests.get(f"{base_url}/", timeout=10)
        if gateway_response.status_code == 200:
            print("   ✅ API Gateway работает")
        else:
            print(f"   ❌ API Gateway: {gateway_response.status_code}")
            results["overall"] = "FAIL"
    except Exception as e:
        print(f"   ❌ API Gateway недоступен: {e}")
        results["overall"] = "FAIL"
    
    # 3. Тестирование аутентификации
    print("\n3. 🔐 Тестирование аутентификации...")
    try:
        auth_response = requests.get(f"{base_url}/api/auth/", timeout=10)
        if auth_response.status_code == 200:
            print("   ✅ Auth Service работает")
        else:
            print(f"   ❌ Auth Service: {auth_response.status_code}")
    except Exception as e:
        print(f"   ❌ Auth Service недоступен: {e}")
    
    # 4. Тестирование загрузки фото
    print("\n4. 📷 Тестирование сервиса загрузки фото...")
    try:
        upload_response = requests.get(f"{base_url}/api/photo_upload/", timeout=10)
        if upload_response.status_code == 200:
            print("   ✅ Photo Upload Service работает")
        else:
            print(f"   ❌ Photo Upload Service: {upload_response.status_code}")
    except Exception as e:
        print(f"   ❌ Photo Upload Service недоступен: {e}")
    
    # 5. Тестирование CV обработки
    print("\n5. 🤖 Тестирование CV Processing Service...")
    try:
        cv_response = requests.get(f"{base_url}/api/cv_processing/", timeout=10)
        if cv_response.status_code == 200:
            print("   ✅ CV Processing Service работает")
        else:
            print(f"   ❌ CV Processing Service: {cv_response.status_code}")
    except Exception as e:
        print(f"   ❌ CV Processing Service недоступен: {e}")
    
    # 6. Тестирование геокодирования
    print("\n6. 🗺️ Тестирование Geocoding Service...")
    try:
        geo_response = requests.get(f"{base_url}/api/geocoding/", timeout=10)
        if geo_response.status_code == 200:
            print("   ✅ Geocoding Service работает")
            
            # Тест геокодирования
            test_geo = requests.get(f"{base_url}/api/geocoding/geocode", 
                                  params={"address": "Москва, Красная площадь"}, 
                                  timeout=10)
            if test_geo.status_code == 200:
                print("   ✅ Геокодирование работает")
            else:
                print(f"   ❌ Геокодирование: {test_geo.status_code}")
                
        else:
            print(f"   ❌ Geocoding Service: {geo_response.status_code}")
    except Exception as e:
        print(f"   ❌ Geocoding Service недоступен: {e}")
    
    # 7. Тестирование фронтенда
    print("\n7. 🎨 Тестирование Frontend...")
    try:
        frontend_response = requests.get("http://localhost:3000", timeout=10)
        if frontend_response.status_code == 200:
            print("   ✅ Frontend работает")
        else:
            print(f"   ❌ Frontend: {frontend_response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend недоступен: {e}")
        results["overall"] = "FAIL"
    
    # 8. Проверка базы данных
    print("\n8. 🗄️ Проверка подключения к БД...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="geo_photo_db",
            user="admin",
            password="admin123"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        print(f"   ✅ База данных подключена, таблиц: {table_count}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ❌ Ошибка подключения к БД: {e}")
        results["overall"] = "FAIL"
    
    # Итоги
    print("\n" + "="*50)
    print("📋 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"Общий статус: {results['overall']}")
    print(f"Проверено сервисов: {len(results['services'])}")
    
    healthy_services = [s for s, status in results['services'].items() if status == 'healthy']
    print(f"Работающих сервисов: {len(healthy_services)}")
    
    if results['overall'] == 'PASS':
        print("🎉 ВСЕ СИСТЕМЫ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ В СИСТЕМЕ")
    
    # Сохраняем результаты
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("📄 Результаты сохранены в test_results.json")

if __name__ == "__main__":
    test_system()