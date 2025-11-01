"""
Blockchain Explorer Service
"""
from typing import Dict, Any, Optional
import aiohttp
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class BlockchainExplorerService:
    """Service for interacting with blockchain explorers to fetch contract source code"""
    
    def __init__(self):
        self.api_keys = {
            "ethereum": settings.ETHERSCAN_API_KEY,
            "bsc": settings.BSCSCAN_API_KEY,
            "polygon": settings.POLYGONSCAN_API_KEY,
            "arbitrum": settings.ARBISCAN_API_KEY,
        }
        
        self.base_urls = {
            "ethereum": "https://api.etherscan.io/api",
            "bsc": "https://api.bscscan.com/api",
            "polygon": "https://api.polygonscan.com/api",
            "arbitrum": "https://api.arbiscan.io/api",
        }
    
    async def get_contract_source(
        self, 
        contract_address: str, 
        network: str = "ethereum"
    ) -> Optional[Dict[str, Any]]:
        """
        Get contract source code from blockchain explorer
        
        Args:
            contract_address: The contract address to fetch
            network: Blockchain network (ethereum, bsc, polygon, arbitrum)
            
        Returns:
            Dictionary with contract information or None if not found
        """
        
        if network not in self.base_urls:
            raise ValueError(f"Unsupported network: {network}")
        
        base_url = self.base_urls[network]
        api_key = self.api_keys.get(network, "")
        
        # Build API request parameters
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address,
            "apikey": api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Explorer API returned status {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if data.get("status") != "1":
                        logger.warning(f"Contract not verified or address invalid: {contract_address}")
                        return None
                    
                    result = data.get("result", [])
                    if not result:
                        return None
                    
                    contract_data = result[0]
                    
                    # Parse and format the response
                    return {
                        "contract_address": contract_address,
                        "network": network,
                        "contract_name": contract_data.get("ContractName"),
                        "compiler_version": contract_data.get("CompilerVersion"),
                        "optimization_enabled": contract_data.get("OptimizationUsed") == "1",
                        "optimization_runs": contract_data.get("Runs"),
                        "constructor_arguments": contract_data.get("ConstructorArguments"),
                        "evm_version": contract_data.get("EVMVersion"),
                        "library_name": contract_data.get("Library"),
                        "library_type": contract_data.get("LibraryType"),
                        "license_type": contract_data.get("LicenseType"),
                        "proxy": contract_data.get("Proxy") == "1",
                        "implementation": contract_data.get("Implementation"),
                        "source_code": self._clean_source_code(contract_data.get("SourceCode", "")),
                        "abi": contract_data.get("ABI"),
                        "creation_date": contract_data.get("CreationDate"),
                        "verified_at": datetime.utcnow().isoformat()
                    }
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching contract source: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching contract source: {str(e)}")
            return None
    
    def _clean_source_code(self, source_code: str) -> str:
        """Clean and format source code from explorer response"""
        
        if not source_code:
            return ""
        
        # Remove common formatting issues from explorer responses
        # Handle single file contracts
        if not source_code.startswith("{") and not source_code.endswith("}"):
            return source_code.strip()
        
        # Handle multi-file contracts (JSON format)
        try:
            import json
            if source_code.startswith("{"):
                contract_data = json.loads(source_code)
                
                # Extract source files and combine them
                sources = contract_data.get("sources", {})
                
                if sources:
                    # Combine all source files
                    combined_code = ""
                    for file_path, file_data in sources.items():
                        file_content = file_data.get("content", "")
                        combined_code += f"\n// File: {file_path}\n{file_content}\n"
                    
                    return combined_code.strip()
                else:
                    # Fallback to any available content
                    return str(contract_data)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return as-is
            return source_code.strip()
        
        return source_code.strip()
    
    async def verify_contract(
        self, 
        contract_address: str, 
        network: str = "ethereum"
    ) -> Dict[str, Any]:
        """
        Verify if contract is verified and get basic info
        
        Args:
            contract_address: Contract address to verify
            network: Blockchain network
            
        Returns:
            Verification status and basic contract info
        """
        
        contract_data = await self.get_contract_source(contract_address, network)
        
        if contract_data:
            return {
                "is_verified": True,
                "contract_address": contract_address,
                "network": network,
                "contract_name": contract_data.get("contract_name"),
                "compiler_version": contract_data.get("compiler_version"),
                "verified_at": contract_data.get("verified_at")
            }
        else:
            return {
                "is_verified": False,
                "contract_address": contract_address,
                "network": network,
                "error": "Contract not verified or not found"
            }
    
    async def get_contract_abi(
        self, 
        contract_address: str, 
        network: str = "ethereum"
    ) -> Optional[str]:
        """
        Get contract ABI from blockchain explorer
        
        Args:
            contract_address: Contract address
            network: Blockchain network
            
        Returns:
            Contract ABI as JSON string or None if not found
        """
        
        if network not in self.base_urls:
            raise ValueError(f"Unsupported network: {network}")
        
        base_url = self.base_urls[network]
        api_key = self.api_keys.get(network, "")
        
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if data.get("status") != "1":
                        return None
                    
                    return data.get("result", "")
        
        except Exception as e:
            logger.error(f"Error fetching contract ABI: {str(e)}")
            return None
    
    async def get_contract_creation_info(
        self, 
        contract_address: str, 
        network: str = "ethereum"
    ) -> Optional[Dict[str, Any]]:
        """
        Get contract creation transaction information
        
        Args:
            contract_address: Contract address
            network: Blockchain network
            
        Returns:
            Creation transaction info or None if not found
        """
        
        if network not in self.base_urls:
            raise ValueError(f"Unsupported network: {network}")
        
        base_url = self.base_urls[network]
        api_key = self.api_keys.get(network, "")
        
        params = {
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": contract_address,
            "apikey": api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if data.get("status") != "1":
                        return None
                    
                    result = data.get("result", [])
                    if not result:
                        return None
                    
                    creation_data = result[0]
                    
                    return {
                        "contract_address": contract_address,
                        "creator_address": creation_data.get("contractCreator"),
                        "creation_transaction": creation_data.get("txHash"),
                        "creation_block": creation_data.get("blockNumber"),
                        "creation_timestamp": creation_data.get("timestamp")
                    }
        
        except Exception as e:
            logger.error(f"Error fetching contract creation info: {str(e)}")
            return None
    
    async def validate_address(self, contract_address: str, network: str = "ethereum") -> bool:
        """
        Validate if address exists on the specified network
        
        Args:
            contract_address: Address to validate
            network: Blockchain network
            
        Returns:
            True if address exists, False otherwise
        """
        
        # Basic address format validation
        if not contract_address.startswith("0x") or len(contract_address) != 42:
            return False
        
        try:
            # Try to get contract creation info as a validation method
            creation_info = await self.get_contract_creation_info(contract_address, network)
            return creation_info is not None
        
        except Exception:
            return False
    
    def get_supported_networks(self) -> Dict[str, str]:
        """Get list of supported networks and their display names"""
        
        return {
            "ethereum": "Ethereum Mainnet",
            "bsc": "Binance Smart Chain",
            "polygon": "Polygon Mainnet",
            "arbitrum": "Arbitrum One"
        }
    
    def get_explorer_url(self, contract_address: str, network: str = "ethereum") -> str:
        """Get the explorer URL for a contract address"""
        
        explorer_urls = {
            "ethereum": f"https://etherscan.io/address/{contract_address}",
            "bsc": f"https://bscscan.com/address/{contract_address}",
            "polygon": f"https://polygonscan.com/address/{contract_address}",
            "arbitrum": f"https://arbiscan.io/address/{contract_address}"
        }
        
        return explorer_urls.get(network, f"https://etherscan.io/address/{contract_address}")
