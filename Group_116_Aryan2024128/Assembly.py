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