# Add blockchain explorer API keys to configuration
ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
BSCSCAN_API_KEY: str = os.getenv("BSCSCAN_API_KEY", "")
POLYGONSCAN_API_KEY: str = os.getenv("POLYGONSCAN_API_KEY", "")
ARBISCAN_API_KEY: str = os.getenv("ARBISCAN_API_KEY", "")

# Blockchain explorer settings
BLOCKCHAIN_EXPLORER_TIMEOUT: int = int(os.getenv("BLOCKCHAIN_EXPLORER_TIMEOUT", "30"))
BLOCKCHAIN_EXPLORER_RATE_LIMIT: int = int(os.getenv("BLOCKCHAIN_EXPLORER_RATE_LIMIT", "5"))  # requests per second
