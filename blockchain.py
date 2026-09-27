import hashlib
import json
import time
from uuid import uuid4

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
        """
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof
        :param last_proof: Previous Proof
        :param proof: Current Proof
        :param last_hash: The hash of the Previous Block
        :return: True if correct, False if not.
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# CLI Interface for Presentation
def run_presentation():
    print("=========================================")
    print(" [INIT: TECH CLUB BLOCKCHAIN PROTOTYPE] ")
    print("=========================================\n")
    
    blockchain = Blockchain()
    print("[*] Genesis block initialized.")
    time.sleep(1)
    
    print("\n[*] Adding new transactions to the memory pool...")
    blockchain.new_transaction("Alice", "Bob", 50)
    blockchain.new_transaction("Bob", "Charlie", 25)
    time.sleep(1)
    print(f"    -> Added 2 transactions. Waiting for miner...")
    
    print("\n[*] Starting Proof of Work (Mining)...")
    last_block = blockchain.last_block
    
    start_time = time.time()
    proof = blockchain.proof_of_work(last_block)
    end_time = time.time()
    
    print(f"    -> [*] Block mined in {round(end_time - start_time, 4)} seconds!")
    print(f"    -> Proof found: {proof}")
    
    # Reward for mining
    blockchain.new_transaction(
        sender="0", # "0" signifies newly mined coins
        recipient="My_Node",
        amount=1,
    )
    
    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    
    print("\n[*] New Block successfully forged and added to the chain!")
    
    print("\n=========================================")
    print(" [BLOCKCHAIN LEDGER STATE] ")
    print("=========================================")
    print(json.dumps(blockchain.chain, indent=4))
    print("\n[*] Presentation complete. Ready for questions.")

if __name__ == '__main__':
    run_presentation()
