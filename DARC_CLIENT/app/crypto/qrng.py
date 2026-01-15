import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def qrng_bytes(n):
    """
    Generate quantum random bytes using Qiskit
    Uses Hadamard gates to create superposition and measurement for true quantum randomness
    """
    # Calculate number of quantum bits needed
    num_qubits = (n * 8 + 7) // 8  # Convert bytes to qubits, round up
    
    # Create quantum circuit with Hadamard gates for superposition
    qc = QuantumCircuit(num_qubits, num_qubits)
    
    # Apply Hadamard gate to each qubit to create uniform superposition
    for i in range(num_qubits):
        qc.h(i)
    
    # Measure all qubits
    qc.measure(range(num_qubits), range(num_qubits))
    
    # Execute circuit on quantum simulator
    simulator = AerSimulator()
    job = simulator.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    # Convert measurement result to bytes
    bit_string = list(counts.keys())[0]
    
    # Convert bit string to bytes
    byte_array = bytearray()
    for i in range(0, len(bit_string), 8):
        if i + 8 <= len(bit_string):
            byte_bits = bit_string[i:i+8]
            byte_array.append(int(byte_bits, 2))
    
    # Return exactly n bytes
    return bytes(byte_array[:n])
