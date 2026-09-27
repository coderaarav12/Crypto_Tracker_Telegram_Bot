module.exports = {
  apps: [
    {
      name: 'crypto-api',
      script: 'api_server.py',
      interpreter: 'python3',
      watch: false,
      env: {
        NODE_ENV: 'production',
      }
    },
    {
      name: 'crypto-bot',
      script: 'telegram_bot.py',
      interpreter: 'python3',
      watch: false,
      env_file: '.env'
    }
  ]
};
