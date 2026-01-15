import numpy as np
from crypto.qrng import qrng_bytes
from crypto.key_derivation import derive_key
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def bb84_generate():
    """
    Generate quantum key using BB84 protocol simulation
    Returns a derived key from quantum measurements
    """
    raw = qrng_bytes(32)
    return derive_key(raw)

def bb84_protocol(key_length=256):
    """
    Full BB84 quantum key distribution protocol
    Simulates Alice and Bob's quantum communication
    
    Args:
        key_length: Desired key length in bits
        
    Returns:
        tuple: (shared_key, alice_basis, bob_basis, error_rate)
    """
    # Step 1: Alice generates random bits and bases
    alice_bits = []
    alice_basis = []
    
    for _ in range(key_length):
        # Random bit (0 or 1)
        bit = int.from_bytes(qrng_bytes(1), 'big') % 2
        # Random basis (0: Z-basis, 1: X-basis)
        basis = int.from_bytes(qrng_bytes(1), 'big') % 2
        
        alice_bits.append(bit)
        alice_basis.append(basis)
    
    # Step 2: Alice prepares quantum states
    alice_states = []
    for bit, basis in zip(alice_bits, alice_basis):
        if basis == 0:  # Z-basis
            # |0⟩ for bit 0, |1⟩ for bit 1
            state = bit
        else:  # X-basis
            # |+⟩ for bit 0, |-⟩ for bit 1
            state = 2 + bit  # 2: |+⟩, 3: |-⟩
        alice_states.append(state)
    
    # Step 3: Bob measures in random bases
    bob_basis = []
    bob_measurements = []
    
    for i, state in enumerate(alice_states):
        # Bob chooses random basis
        basis = int.from_bytes(qrng_bytes(1), 'big') % 2
        bob_basis.append(basis)
        
        # Create quantum circuit for measurement
        qc = QuantumCircuit(1, 1)
        
        # Prepare Alice's state
        if state == 0:  # |0⟩
            pass  # Already in |0⟩
        elif state == 1:  # |1⟩
            qc.x(0)
        elif state == 2:  # |+⟩
            qc.h(0)
        elif state == 3:  # |-⟩
            qc.h(0)
            qc.x(0)
        
        # Bob measures in his chosen basis
        if basis == 1:  # X-basis
            qc.h(0)
        
        qc.measure(0, 0)
        
        # Execute measurement
        simulator = AerSimulator()
        job = simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Get measurement result
        measurement = int(list(counts.keys())[0], 2)
        bob_measurements.append(measurement)
    
    # Step 4: Sifting - keep only measurements with same basis
    shared_key = []
    matching_indices = []
    
    for i in range(key_length):
        if alice_basis[i] == bob_basis[i]:
            shared_key.append(bob_measurements[i])
            matching_indices.append(i)
    
    # Step 5: Error estimation (sample some bits)
    if len(shared_key) > 10:
        sample_size = min(10, len(shared_key) // 4)
        sample_indices = np.random.choice(len(shared_key), sample_size, replace=False)
        
        # In real implementation, Alice and Bob would compare these over public channel
        # For simulation, we'll calculate the actual error rate
        errors = 0
        for idx in sample_indices:
            original_idx = matching_indices[idx]
            if alice_bits[original_idx] != shared_key[idx]:
                errors += 1
        
        error_rate = errors / sample_size
        
        # Remove sampled bits from final key
        final_key = [bit for i, bit in enumerate(shared_key) if i not in sample_indices]
    else:
        final_key = shared_key
        error_rate = 0.0
    
    # Convert key bits to bytes
    if len(final_key) > 0:
        key_bytes = bytearray()
        for i in range(0, len(final_key), 8):
            if i + 8 <= len(final_key):
                byte_bits = final_key[i:i+8]
                byte = 0
                for j, bit in enumerate(byte_bits):
                    byte |= bit << (7 - j)
                key_bytes.append(byte)
        
        shared_key_bytes = bytes(key_bytes)
    else:
        shared_key_bytes = b'\x00' * 32  # Fallback
    
    return derive_key(shared_key_bytes), alice_basis, bob_basis, error_rate

def create_bb84_circuit(bit, basis):
    """
    Create a quantum circuit for BB84 protocol
    
    Args:
        bit: The bit value (0 or 1)
        basis: The basis (0: Z-basis, 1: X-basis)
        
    Returns:
        QuantumCircuit: Prepared quantum state
    """
    qc = QuantumCircuit(1, 1)
    
    # Prepare the bit in the correct basis
    if bit == 1:
        qc.x(0)
    
    if basis == 1:  # X-basis
        qc.h(0)
    
    return qc

def measure_bb84_circuit(qc, basis):
    """
    Measure a BB84 quantum circuit in the specified basis
    
    Args:
        qc: Quantum circuit to measure
        basis: Measurement basis (0: Z-basis, 1: X-basis)
        
    Returns:
        int: Measurement result (0 or 1)
    """
    # Create a copy of the circuit for measurement
    measure_circuit = qc.copy()
    
    # Measure in the specified basis
    if basis == 1:  # X-basis
        measure_circuit.h(0)
    
    measure_circuit.measure(0, 0)
    
    # Execute measurement
    simulator = AerSimulator()
    job = simulator.run(measure_circuit, shots=1)
    result = job.result()
    counts = result.get_counts(measure_circuit)
    
    return int(list(counts.keys())[0], 2)
