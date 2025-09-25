import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dcam-production-secret-key-2025'
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}