
register_map = {
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011",
    "tp": "00100", "t0": "00101", "t1": "00110", "t2": "00111",
    "s0": "01000", "s1": "01001", "a0": "01010", "a1": "01011",
    "a2": "01100", "a3": "01101", "a4": "01110", "a5": "01111",
    "a6": "10000", "a7": "10001", "s2": "10010", "s3": "10011",
    "s4": "10100", "s5": "10101", "s6": "10110", "s7": "10111",
    "s8": "11000", "s9": "11001", "s10": "11010", "s11": "11011",
    "t3": "11100", "t4": "11101", "t5": "11110", "t6": "11111"
}

def parse_assembly(lines):
    labels = {}
    variables = {}
    instructions = []
    var_address = 256

  
    memory_address = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("var"):
            continue

        label = None
        if ':' in line:
            possible_label, sep, rest = line.partition(':')
            possible_label = possible_label.strip()
            rest = rest.strip()
            if possible_label and ' ' not in possible_label:
                label = possible_label
                line = rest

        tokens = []
        for token in line.split():
            split_tokens = token.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
            tokens.extend(split_tokens)

        if label is not None:
            labels[label] = memory_address

        if tokens:
            memory_address += 1

    
    memory_address = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("var"):
            parts = line.split()
            variables[parts[1]] = var_address
            var_address += 1
            continue

        label = None
        if ':' in line:
            possible_label, sep, rest = line.partition(':')
            possible_label = possible_label.strip()
            rest = rest.strip()
            if possible_label and ' ' not in possible_label:
                label = possible_label
                line = rest

        tokens = []
        for token in line.split():
            split_tokens = token.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
            tokens.extend(split_tokens)

        if tokens:
            if tokens[0] in ["lw", "sw"] and len(tokens) >= 3:
                parts = tokens[-1].split('(')
                if len(parts) == 2:
                    offset = parts[0]
                    base_reg = parts[1].strip(')')
                    tokens = tokens[:-1] + [offset, base_reg]
            instructions.append(tokens)
            memory_address += 1

    return instructions, labels, variables


def i_type(instruction, opcode, funct3):
    try:
        imm = format(int(instruction[3]), '012b')
    except ValueError:
        print(f"Error: Invalid immediate '{instruction[3]}' in instruction: {' '.join(instruction)}")
        exit(1)
    return imm + register_map[instruction[2]] + funct3 + register_map[instruction[1]] + opcode

def s_type(instruction, opcode, funct3):
    try:
        imm = format(int(instruction[3]), '012b')
    except ValueError:
        print(f"Error: Invalid immediate '{instruction[3]}' in instruction: {' '.join(instruction)}")
        exit(1)
    return imm[:7] + register_map[instruction[2]] + register_map[instruction[1]] + funct3 + imm[7:] + opcode

def b_type(instruction, opcode, funct3, current_address, labels):
    imm = calculate_branch_offset(instruction[3], labels, current_address)
    return (imm[0] + imm[2:8] + register_map[instruction[2]] + 
            register_map[instruction[1]] + funct3 + imm[8:] + imm[1] + opcode)

def j_type(instruction, opcode, current_address, labels):
    target = instruction[2]
    if target in labels:
        imm = labels[target] - current_address
    else:
        imm = int(target)
    
    validate_immediate(imm, 20)
    imm_bin = format(imm & 0xFFFFF, '020b')
    encoded_imm = imm_bin[0] + imm_bin[10:20] + imm_bin[9] + imm_bin[1:9]
    return encoded_imm + register_map[instruction[1]] + opcode

def assemble_instruction(instruction, labels, variables, current_address):
    opcode_map = {
        "add": {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
        "sub": {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
        "mul": {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000001"},
        "xor": {"type": "R", "opcode": "0110011", "funct3": "100", "funct7": "0000000"},
        "or": {"type": "R", "opcode": "0110011", "funct3": "110", "funct7": "0000000"},
        "and": {"type": "R", "opcode": "0110011", "funct3": "111", "funct7": "0000000"},
        "slt": {"type": "R", "opcode": "0110011", "funct3": "010", "funct7": "0000000"},
        "lw": {"type": "I", "opcode": "0000011", "funct3": "010"},
        "sw": {"type": "S", "opcode": "0100011", "funct3": "010"},
        "addi": {"type": "I", "opcode": "0010011", "funct3": "000"},
        "srl": {"type": "R", "opcode": "0110011", "funct3": "101", "funct7": "0000000"},
        "jalr": {"type": "I", "opcode": "1100111", "funct3": "000"},
        "beq": {"type": "B", "opcode": "1100011", "funct3": "000"},
        "bne": {"type": "B", "opcode": "1100011", "funct3": "001"},
        "jal": {"type": "J", "opcode": "1101111"},
        "hlt": {"type": "H", "opcode": "1110011"}
    }

    op = instruction[0]
    if op not in opcode_map:
        print(f"Error: Unsupported instruction '{op}'")
        exit(1)

    info = opcode_map[op]
    if info["type"] == "R":
        for operand in instruction[1:4]:
            if operand not in register_map:
                print(f"Error: Invalid register '{operand}' in instruction: {' '.join(instruction)}")
                exit(1)
        return r_type(instruction, info["opcode"], info["funct3"], info["funct7"])
    elif info["type"] == "I":
        if op == "lw":
            reordered = [instruction[0], instruction[1], instruction[3], instruction[2]]
            instruction = reordered
        return i_type(instruction, info["opcode"], info["funct3"])
    elif info["type"] == "S":
        reordered = [instruction[0], instruction[1], instruction[3], instruction[2]]
        instruction = reordered
        return s_type(instruction, info["opcode"], info["funct3"])
    elif info["type"] == "B":
        return b_type(instruction, info["opcode"], info["funct3"], current_address, labels)
    elif info["type"] == "J":
        return j_type(instruction, info["opcode"], current_address, labels)
    elif info["type"] == "H":
        return info["opcode"] + "0"*20
    else:
        print(f"Error: Unknown instruction type {info['type']}")
        exit(1)

def main():
    input_file = 'input.txt'
    output_file = 'output.txt'

    with open(input_file, 'r') as f:
        lines = f.readlines()

    instructions, labels, variables = parse_assembly(lines)
    binary_code = []

    for current_address, instr in enumerate(instructions):
        binary_instr = assemble_instruction(instr, labels, variables, current_address)
        binary_code.append(binary_instr)

    with open(output_file, 'w') as f:
        for code in binary_code:
            f.write(code + '\n')

if __name__ == "__main__":
    main()
