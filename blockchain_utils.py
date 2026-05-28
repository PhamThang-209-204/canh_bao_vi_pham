import hashlib
import json
import os
from web3 import Web3
import solcx

def generate_image_hash(filepath):
    """Đọc file ảnh và tạo mã băm SHA256"""
    if not os.path.exists(filepath):
        print(f"File không tồn tại: {filepath}")
        return None
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Đọc theo từng block để tiết kiệm bộ nhớ với file lớn
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    return sha256_hash.hexdigest()

class BlockchainManager:
    def __init__(self, rpc_url="http://127.0.0.1:8545", contract_source_path="TrafficViolation.sol"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_source_path = contract_source_path
        self.contract = None
        self.account = None
        
        # Thử kết nối
        if self.w3.is_connected():
            print(f"Đã kết nối thành công tới Blockchain: {rpc_url}")
            self.account = self.w3.eth.accounts[0] # Sử dụng account đầu tiên trong Ganache
        else:
            print(f"Không thể kết nối tới Blockchain: {rpc_url}. Hãy chắc chắn Ganache đang chạy.")
            
    def _compile_contract(self):
        print("Đang biên dịch Smart Contract...")
        try:
            # Cài đặt solc nếu chưa có (lần đầu sẽ hơi lâu)
            if '0.8.0' not in solcx.get_installed_solc_versions():
                print("Đang tải solc version 0.8.0...")
                solcx.install_solc('0.8.0')
            solcx.set_solc_version('0.8.0')
        except Exception as e:
            print(f"Lỗi khi cài đặt/thiết lập solc: {e}")
            
        with open(self.contract_source_path, "r") as f:
            contract_source_code = f.read()

        compiled_sol = solcx.compile_standard(
            {
                "language": "Solidity",
                "sources": {"TrafficViolation.sol": {"content": contract_source_code}},
                "settings": {
                    "outputSelection": {
                        "*": {
                            "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                        }
                    }
                },
            },
            solc_version="0.8.0",
        )

        bytecode = compiled_sol["contracts"]["TrafficViolation.sol"]["TrafficViolation"]["evm"]["bytecode"]["object"]
        abi = json.loads(compiled_sol["contracts"]["TrafficViolation.sol"]["TrafficViolation"]["metadata"])["output"]["abi"]
        return abi, bytecode

    def deploy_contract(self):
        if not self.w3.is_connected():
            return False
            
        abi, bytecode = self._compile_contract()
        TrafficViolationContract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        print("Đang deploy Smart Contract...")
        tx_hash = TrafficViolationContract.constructor().transact({'from': self.account})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        self.contract = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
        print(f"Deploy thành công! Contract Address: {self.contract.address}")
        
        # Lưu lại địa chỉ contract và abi để dùng sau này (trong verify)
        with open("contract_address.json", "w") as f:
            json.dump({"address": self.contract.address, "abi": abi}, f)
            
        return True
        
    def load_contract(self):
        if os.path.exists("contract_address.json"):
            with open("contract_address.json", "r") as f:
                data = json.load(f)
                self.contract = self.w3.eth.contract(address=data["address"], abi=data["abi"])
            print(f"Đã load contract từ địa chỉ: {self.contract.address}")
            return True
        else:
            print("Chưa có contract được deploy trước đó. Tiến hành deploy mới...")
            return self.deploy_contract()

    def add_violation(self, violation_id, vehicle_id, speed, timestamp, image_hash):
        if not self.contract:
            if not self.load_contract():
                return None
                
        print(f"Đang lưu dữ liệu vi phạm {violation_id} lên Blockchain...")
        tx_hash = self.contract.functions.addViolation(
            violation_id,
            int(vehicle_id),
            str(speed),
            str(timestamp),
            str(image_hash)
        ).transact({'from': self.account})
        
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Lưu thành công! TxHash: {tx_receipt.transactionHash.hex()}")
        return tx_receipt.transactionHash.hex()

    def get_violation(self, violation_id):
        if not self.contract:
            if not self.load_contract():
                return None
        try:
            result = self.contract.functions.getViolation(violation_id).call()
            # Trả về: vehicleId, speed, timestamp, imageHash
            return {
                "vehicleId": result[0],
                "speed": result[1],
                "timestamp": result[2],
                "imageHash": result[3]
            }
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu từ blockchain: {e}")
            return None
