#!/usr/bin/env python3
"""
Health check simple para Railway
"""

def health_check():
    """Verificación básica de salud"""
    try:
        from api_colaborativa import app
        return {"status": "healthy", "message": "API funcional"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = health_check()
    print(f"Health Check: {result}") 