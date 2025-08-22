#!/usr/bin/env python3
"""
Script para verificar que todos los archivos URLs estén bien configurados
"""

import os
import sys

def check_url_file(app_name):
    """Verificar que un archivo de URLs esté bien configurado"""
    file_path = f"apps/{app_name}/urls.py"
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} no existe")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificaciones básicas
        if 'urlpatterns' not in content:
            print(f"❌ {file_path} no tiene 'urlpatterns'")
            return False
        
        if 'from django.urls import' not in content:
            print(f"❌ {file_path} no importa django.urls")
            return False
        
        print(f"✅ {file_path} OK")
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo {file_path}: {e}")
        return False

def main():
    """Verificar todas las apps"""
    apps = ['users', 'businesses', 'orders', 'tracking', 'payments', 'notifications']
    
    print("🔍 Verificando archivos URLs...")
    print("-" * 50)
    
    all_ok = True
    for app in apps:
        if not check_url_file(app):
            all_ok = False
    
    print("-" * 50)
    if all_ok:
        print("✅ Todos los archivos URLs están OK")
        print("\n🚀 Puedes ejecutar: python manage.py runserver")
    else:
        print("❌ Hay problemas con algunos archivos URLs")
        print("\n📝 Crea los archivos faltantes y ejecuta este script de nuevo")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())