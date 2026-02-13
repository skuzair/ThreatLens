from web3 import Web3
from web3.middleware import geth_poa_middleware
import hashlib
import json
from config import settings
from typing import Dict, List


class BlockchainService:
    """Service for anchoring evidence to Polygon blockchain"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        # Required for Polygon
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if settings.POLYGON_PRIVATE_KEY:
            self.wallet = self.w3.eth.account.from_key(settings.POLYGON_PRIVATE_KEY)
        else:
            self.wallet = None
            print("⚠️ No blockchain private key configured")
        
        # Simple evidence registry contract ABI
        self.contract_abi = [
            {
                "inputs": [{"type": "bytes32", "name": "evidenceHash"}],
                "name": "registerEvidence",
                "outputs": [{"type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"type": "bytes32", "name": "evidenceHash"}],
                "name": "verifyEvidence",
                "outputs": [
                    {"type": "bool", "name": "exists"},
                    {"type": "uint256", "name": "timestamp"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        if settings.POLYGON_CONTRACT_ADDRESS:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.POLYGON_CONTRACT_ADDRESS),
                abi=self.contract_abi
            )
        else:
            self.contract = None
            print("⚠️ No blockchain contract address configured")
    
    def compute_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of a file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def compute_hash_from_bytes(self, data: bytes) -> str:
        """Compute SHA256 hash from bytes"""
        return hashlib.sha256(data).hexdigest()
    
    async def anchor_evidence(self, evidence_manifest: Dict) -> List[Dict]:
        """
        Anchor evidence hashes to blockchain
        Returns list of transaction receipts
        """
        if not self.wallet or not self.contract:
            print("⚠️ Blockchain not configured, skipping anchoring")
            return []
        
        receipts = []
        
        try:
            for evidence_type, evidence_data in evidence_manifest.get("evidence", {}).items():
                file_path = evidence_data.get("file_path")
                if not file_path:
                    continue
                
                # Compute file hash
                file_hash = evidence_data.get("sha256") or self.compute_hash(file_path)
                hash_bytes = bytes.fromhex(file_hash)
                
                # Build transaction
                tx = self.contract.functions.registerEvidence(hash_bytes).build_transaction({
                    "from": self.wallet.address,
                    "nonce": self.w3.eth.get_transaction_count(self.wallet.address),
                    "gas": 100000,
                    "gasPrice": self.w3.to_wei("30", "gwei"),
                    "chainId": settings.POLYGON_CHAIN_ID
                })
                
                # Sign and send
                signed = self.wallet.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
                
                # Wait for receipt
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                receipts.append({
                    "file": file_path,
                    "evidence_type": evidence_type,
                    "sha256": file_hash,
                    "tx_hash": receipt["transactionHash"].hex(),
                    "block_number": receipt["blockNumber"],
                    "polygonscan_url": f"https://mumbai.polygonscan.com/tx/{receipt['transactionHash'].hex()}"
                })
                
                print(f"✅ Evidence anchored: {evidence_type} | Block: {receipt['blockNumber']}")
        
        except Exception as e:
            print(f"❌ Error anchoring evidence: {e}")
        
        return receipts
    
    def verify_evidence(self, file_hash: str) -> Dict:
        """
        Verify if evidence hash exists on blockchain
        Returns verification result
        """
        if not self.contract:
            return {
                "verified": False,
                "error": "Blockchain not configured"
            }
        
        try:
            hash_bytes = bytes.fromhex(file_hash)
            exists, timestamp = self.contract.functions.verifyEvidence(hash_bytes).call()
            
            return {
                "verified": exists,
                "timestamp": timestamp,
                "hash": file_hash
            }
        
        except Exception as e:
            print(f"❌ Error verifying evidence: {e}")
            return {
                "verified": False,
                "error": str(e)
            }


# Global instance
blockchain_service = BlockchainService()
