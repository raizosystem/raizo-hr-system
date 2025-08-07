import requests
import json

def test_notifications_api():
    try:
        # فحص API الإشعارات
        response = requests.get('http://127.0.0.1:5000/api/notifications')
        print(f"حالة الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"البيانات المستلمة: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"خطأ في API: {response.text}")
            
    except Exception as e:
        print(f"خطأ في الاتصال: {e}")

if __name__ == '__main__':
    test_notifications_api()