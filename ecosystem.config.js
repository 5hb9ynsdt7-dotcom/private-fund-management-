module.exports = {
  apps: [
    {
      name: 'privatefund-backend',
      cwd: './backend',
      script: './backend_venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000 --reload',
      interpreter: 'none',
      env: {
        PYTHONPATH: '.',
      },
      error_file: '../logs/backend-error.log',
      out_file: '../logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
    },
    {
      name: 'privatefund-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run dev',
      env: {
        NODE_ENV: 'development',
      },
      error_file: '../logs/frontend-error.log',
      out_file: '../logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
    }
  ]
};
