import logging
import logging.handlers
import os
from flask import request, has_request_context

class SecurityFormatter(logging.Formatter):
    """
    Custom formatter to include request-specific data like IP and User ID.
    """
    def format(self, record):
        if has_request_context():
            record.ip = request.remote_addr
            # User ID logic can be expanded here if needed
        else:
            record.ip = "N/A"
        return super().format(record)

def setup_logging(app):
    """
    Configure security logging for the Flask application.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "unisplit_security.log")
    
    # 10MB per file, keep 5 backups
    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    
    # Standard format: [Timestamp] [Level] [IP] [Message]
    formatter = SecurityFormatter('%(asctime)s [%(levelname)s] [%(ip)s] %(message)s')
    handler.setFormatter(formatter)
    
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(handler)
    
    app.logger.addHandler(handler)
    return security_logger
