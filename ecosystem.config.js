# Production PM2 Configuration

module.exports = {
    apps: [{
        name: 'indogovrag-api',
        script: 'python',
        args: 'api/main.py',
        cwd: './indoGov',
        instances: 1,  # Start with 1, scale to 3-5 later
    exec_mode: 'fork',  # Use 'cluster' for Node.js only
    autorestart: true,
        watch: false,  # Disable in production
    max_memory_restart: '2G',

        env: {
            NODE_ENV: 'production',
            PYTHONUNBUFFERED: '1',
            OLLAMA_HOST: 'http://localhost:11434',
            REDIS_URL: 'redis://localhost:6379/0'
        },

        error_file: './logs/pm2-error.log',
        out_file: './logs/pm2-out.log',
        log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    
    # Monitoring
    min_uptime: '10s',
        max_restarts: 10,
        autorestart: true,
    
    # Graceful shutdown
    kill_timeout: 5000,
        wait_ready: true,
        listen_timeout: 3000
    }]
}
