import re

# --- FUNÇÃO DE EXTRAÇÃO DE BLOCO REVISADA ---
def parse_appointment_block(block_lines):
    """
    Recebe um bloco de linhas e extrai os campos do agendamento de forma flexível.
    """
    if len(block_lines) < 4:  # Mínimo necessário: hora, paciente, convênio, evento
        return None
    
    EVENT_TYPES = ["CONSULTA", "RETORNO"]
    
    # Inicializar dicionário com valores padrão
    record = {
        "time": "",
        "patient": "",
        "insurance": "",
        "patient_phone": "",
        "event": "",
        "doctor": "",
        "record": ""
    }
    
    # Primeira linha é sempre o horário
    record["time"] = block_lines[0]
    
    # Verificar se a segunda linha contém médico e paciente
    if len(block_lines) > 1:
        # Tentar separar médico e paciente (se estiverem na mesma linha)
        parts = re.split(r'\s{2,}', block_lines[1])
        if len(parts) >= 2:
            record["doctor"] = parts[0].strip()
            record["patient"] = parts[1].strip()
        else:
            record["patient"] = block_lines[1].strip()
    
    # Linhas seguintes podem ser convênio, telefone, evento, etc.
    for i in range(2, min(7, len(block_lines))):  # Verificar até 7 linhas
        line = block_lines[i]
        
        # Verificar se é um número de telefone
        phone_match = re.search(r'\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}', line)
        if phone_match and not record["patient_phone"]:
            record["patient_phone"] = phone_match.group()
            # O restante da linha provavelmente é o convênio
            insurance_part = line.replace(record["patient_phone"], "").strip().rstrip('-').strip()
            if insurance_part and not record["insurance"]:
                record["insurance"] = insurance_part
        
        # Verificar se é um evento
        elif any(event in line.upper() for event in EVENT_TYPES) and not record["event"]:
            record["event"] = line.strip()
        
        # Verificar se é um número de prontuário
        elif re.match(r'\d{2,3}\.\d{2,3}', line) and not record["record"]:
            record["record"] = line.strip()
        
        # Se não for nenhum dos acima, pode ser convênio ou informação adicional
        elif not record["insurance"] and not phone_match:
            record["insurance"] = line.strip().rstrip('-').strip()
    
    return record

# --- CÓDIGO PRINCIPAL ---
texto_completo = items[0]['json']['text']
linhas = [line.strip() for line in texto_completo.split('\n') if line.strip()]

agendamentos_finalizados = []
data_atual = ""
especialidade_atual = ""

# Regex
regex_hora = re.compile(r'^\d{2}:\d{2}$') 
regex_data = re.compile(r'\d{2}/\d{2}/\d{4}')
HEADER_INDICATORS = ("Página", "SIMAH", "Agendamentos de Consultas")
lixo_prefixos = ("Página", "SIMAH", "Agendamentos de Consultas", "COFRAT", "Sub - Total",
                 "Médico", "Paciente", "Convênio", "Telefone do Paciente", "Evento", "Prontuário")

def is_near_header(idx, context_lines=3):
    for k in range(0, context_lines):
        j = idx - k
        if j < 0: break
        if any(ind in linhas[j] for ind in HEADER_INDICATORS):
            return True
    return False

# --- LOOP PRINCIPAL REVISADO ---
i = 0
while i < len(linhas):
    linha = linhas[i]

    # ignora lixo
    if any(linha.startswith(prefixo) for prefixo in lixo_prefixos):
        i += 1
        continue

    # --- captura de data ---
    match_data = regex_data.search(linha)
    if match_data and not is_near_header(i):
        data_atual = match_data.group(0)
        i += 1
        continue

    # --- captura de especialidade ---
    if "Especialidade" in linha:
        parts = linha.split("Especialidade", 1)
        if len(parts) > 1:
            especialidade_atual = parts[1].lstrip(':').strip()
        else:
            if i + 1 < len(linhas):
                especialidade_atual = linhas[i+1].strip()
                i += 1
        i += 1
        continue

    # --- captura de agendamento ---
    if regex_hora.match(linha):
        # Coletar todas as linhas relevantes para este agendamento
        bloco_de_linhas = [linha]  # Começa com a linha do horário
        
        # Coletar linhas subsequentes até encontrar outro horário ou cabeçalho
        j = i + 1
        while j < len(linhas):
            next_line = linhas[j]
            
            # Parar se encontrar outro horário ou cabeçalho
            if regex_hora.match(next_line) or any(next_line.startswith(p) for p in lixo_prefixos):
                break
                
            bloco_de_linhas.append(next_line)
            j += 1
        
        # Processar o bloco
        agendamento = parse_appointment_block(bloco_de_linhas)
        if agendamento:
            agendamento['date'] = data_atual
            agendamento['specialty'] = especialidade_atual
            agendamentos_finalizados.append(agendamento)
        
        # Avançar para a próxima linha após o bloco
        i = j
    else:
        i += 1

# --- RETORNO ---
return [{"json": ag} for ag in agendamentos_finalizados]